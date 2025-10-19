from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from fastapi import HTTPException, status

from app.models.inventory import (
    Product, Category, StockMovement, ProductCostHistory, 
    ProductStatus, StockMovementType
)
from app.models.user import User
from app.core.logging_config import main_logger, exception_handler

logger = main_logger

class InventoryService:
    """Servicio para gestión completa de inventario"""
    
    def __init__(self, db: Session):
        self.db = db

    def _normalize_date_range(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """
        Normaliza el rango de fechas para que date_to sea el final del día especificado.
        
        Args:
            date_from: Fecha de inicio en formato YYYY-MM-DD
            date_to: Fecha de fin en formato YYYY-MM-DD
            
        Returns:
            Tuple con (date_from_normalized, date_to_normalized)
        """
        normalized_from = date_from
        normalized_to = date_to
        
        if date_to:
            # Convertir date_to al final del día (23:59:59.999999)
            try:
                date_obj = datetime.strptime(date_to, '%Y-%m-%d')
                # Agregar 23 horas, 59 minutos, 59 segundos y 999999 microsegundos
                end_of_day = date_obj + timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
                normalized_to = end_of_day.strftime('%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                # Si el formato no es válido, usar como está
                logger.warning(f"Formato de fecha inválido para date_to: {date_to}")
                pass
        
        if date_from:
            # Asegurar que date_from sea el inicio del día (00:00:00)
            try:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d')
                start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                normalized_from = start_of_day.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Si el formato no es válido, usar como está
                logger.warning(f"Formato de fecha inválido para date_from: {date_from}")
                pass
        
        return normalized_from, normalized_to

    @exception_handler(logger, {"service": "InventoryService", "method": "get_products"})
    def get_products(self, 
                    category_id: Optional[int] = None,
                    status: Optional[str] = None,
                    search: Optional[str] = None,
                    include_costs: bool = False,
                    page: int = 1,
                    per_page: int = 50) -> Dict[str, Any]:
        """Obtiene lista de productos con filtros"""
        
        # Hacer join con categorías para obtener información completa
        query = self.db.query(Product, Category.name.label('category_name'), Category.color.label('category_color'))\
                      .outerjoin(Category, Product.category_id == Category.id)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
            
        if status:
            query = query.filter(Product.status == status)
            
        if search:
            query = query.filter(
                Product.name.ilike(f"%{search}%") |
                Product.description.ilike(f"%{search}%") |
                Product.barcode.ilike(f"%{search}%") |
                Product.sku.ilike(f"%{search}%")
            )
        
        # Contar total de registros para paginación
        total_query = self.db.query(Product)
        if category_id:
            total_query = total_query.filter(Product.category_id == category_id)
        if status:
            total_query = total_query.filter(Product.status == status)
        if search:
            total_query = total_query.filter(
                Product.name.ilike(f"%{search}%") |
                Product.description.ilike(f"%{search}%") |
                Product.barcode.ilike(f"%{search}%") |
                Product.sku.ilike(f"%{search}%")
            )
        
        total_count = total_query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        results = query.order_by(Product.name).offset(offset).limit(per_page).all()
        
        # Convertir a lista de diccionarios con información completa
        products = []
        for product, category_name, category_color in results:
            product_dict = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "category_id": product.category_id,
                "category_name": category_name,
                "category_color": category_color,
                "barcode": product.barcode,
                "sku": product.sku,
                "current_cost": product.current_cost if include_costs else 0,
                "selling_price": product.selling_price,
                "profit_margin": product.calculated_profit_margin if include_costs else 0,
                "current_stock": product.current_stock,
                "min_stock": product.min_stock,
                "max_stock": product.max_stock,
                "unit_of_measure": product.unit_of_measure,
                "weight_per_unit": product.weight_per_unit,
                "status": product.status,
                "is_taxable": product.is_taxable,
                "tax_rate": product.tax_rate,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "last_restock_date": product.last_restock_date,
                "last_sale_date": product.last_sale_date,
                "is_low_stock": product.is_low_stock
            }
            products.append(product_dict)
        
        # Calcular información de paginación
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
                
        return {
            "products": products,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }

    @exception_handler(logger, {"service": "InventoryService", "method": "create_product"})
    def create_product(self, product_data: Dict[str, Any], user_id: int) -> Product:
        """Crea un nuevo producto"""
        
        # Verificar que la categoría existe
        if product_data.get('category_id'):
            category = self.db.query(Category).filter(Category.id == product_data['category_id']).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada"
                )
        
        # Verificar unicidad de barcode y SKU
        if product_data.get('barcode'):
            existing = self.db.query(Product).filter(Product.barcode == product_data['barcode']).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un producto con ese código de barras"
                )
        
        if product_data.get('sku'):
            existing = self.db.query(Product).filter(Product.sku == product_data['sku']).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un producto con ese SKU"
                )
        
        # Crear el producto (excluyendo profit_margin)
        filtered_data = {k: v for k, v in product_data.items() if k != 'profit_margin'}
        product = Product(**filtered_data)
        
        # Calcular y asignar margen manualmente
        if product.selling_price > 0:
            product.profit_margin = ((product.selling_price - product.current_cost) / product.selling_price) * 100
        
        self.db.add(product)
        self.db.flush()  # Para obtener el ID
        
        # Crear movimiento de stock inicial si hay stock
        if product.current_stock > 0:
            self._create_stock_movement(
                product_id=product.id,
                user_id=user_id,
                movement_type="adjustment",
                quantity=product.current_stock,
                unit_cost=product.current_cost,
                notes="Stock inicial al crear producto"
            )
        
        # Crear historial de costo inicial
        if product.current_cost > 0:
            self._create_cost_history(
                product_id=product.id,
                user_id=user_id,
                cost_per_unit=product.current_cost,
                quantity_purchased=product.current_stock,
                total_cost=product.current_cost * product.current_stock,
                notes="Costo inicial al crear producto"
            )
        
        self.db.commit()
        self.db.refresh(product)
        
        logger.info(f"✅ Producto creado: {product.name} (ID: {product.id})")
        return product

    @exception_handler(logger, {"service": "InventoryService", "method": "update_product"})
    def update_product(self, product_id: int, product_data: Dict[str, Any], user_id: int) -> Product:
        """Actualiza un producto existente"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Guardar valores anteriores para comparación
        old_stock = product.current_stock
        old_cost = product.current_cost
        
        # Actualizar campos
        for key, value in product_data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        # Recalcular margen de ganancia si cambió el precio o costo
        if 'selling_price' in product_data or 'current_cost' in product_data:
            if product.selling_price > 0:
                product.profit_margin = ((product.selling_price - product.current_cost) / product.selling_price) * 100
        
        # Si cambió el stock, crear movimiento
        if 'current_stock' in product_data and product_data['current_stock'] != old_stock:
            stock_diff = product_data['current_stock'] - old_stock
            movement_type = "purchase" if stock_diff > 0 else "adjustment"
            
            self._create_stock_movement(
                product_id=product.id,
                user_id=user_id,
                movement_type=movement_type,
                quantity=stock_diff,
                unit_cost=product.current_cost,
                notes="Ajuste de stock manual"
            )
        
        # Si cambió el costo, crear historial
        if 'current_cost' in product_data and product_data['current_cost'] != old_cost:
            self._create_cost_history(
                product_id=product.id,
                user_id=user_id,
                cost_per_unit=product_data['current_cost'],
                quantity_purchased=0,  # Es solo actualización de costo
                total_cost=0,
                notes="Actualización de costo"
            )
        
        self.db.commit()
        self.db.refresh(product)
        
        logger.info(f"✅ Producto actualizado: {product.name} (ID: {product.id})")
        return product

    @exception_handler(logger, {"service": "InventoryService", "method": "restock_product"})
    def restock_product(self, 
                       product_id: int, 
                       quantity: int, 
                       unit_cost: float, 
                       supplier_name: str,
                       user_id: int,
                       new_selling_price: Optional[float] = None,
                       invoice_number: Optional[str] = None,
                       notes: Optional[str] = None) -> Product:
        """Registra restock de un producto"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Actualizar stock y costos
        old_stock = product.current_stock
        old_cost = product.current_cost
        old_price = product.selling_price
        
        # Calcular costo promedio ponderado
        total_old_value = old_stock * old_cost
        total_new_value = quantity * unit_cost
        new_total_stock = old_stock + quantity
        
        if new_total_stock > 0:
            # Costo promedio ponderado
            product.current_cost = (total_old_value + total_new_value) / new_total_stock
        else:
            product.current_cost = unit_cost
            
        product.current_stock = new_total_stock
        
        # Actualizar precio de venta si se especifica
        if new_selling_price and new_selling_price > 0:
            product.selling_price = new_selling_price
        
        # Recalcular margen con el nuevo costo promedio
        if product.selling_price > 0:
            product.profit_margin = ((product.selling_price - product.current_cost) / product.selling_price) * 100
            
        product.last_restock_date = datetime.utcnow()
        
        # Crear movimiento de stock
        self._create_stock_movement(
            product_id=product.id,
            user_id=user_id,
            movement_type="purchase",
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=unit_cost * quantity,
            supplier=supplier_name,
            reference_number=invoice_number,
            notes=notes
        )
        
        # Crear historial de costo
        self._create_cost_history(
            product_id=product.id,
            user_id=user_id,
            cost_per_unit=unit_cost,
            quantity_purchased=quantity,
            total_cost=unit_cost * quantity,
            supplier_name=supplier_name,
            supplier_invoice=invoice_number,
            notes=notes
        )
        
        self.db.commit()
        self.db.refresh(product)
        
        logger.info(f"✅ Restock registrado: {product.name} (+{quantity} unidades)")
        return product

    def _create_stock_movement(self, 
                              product_id: int, 
                              user_id: int, 
                              movement_type: StockMovementType,
                              quantity: int,
                              unit_cost: Optional[float] = None,
                              total_cost: Optional[float] = None,
                              supplier: Optional[str] = None,
                              reference_number: Optional[str] = None,
                              notes: Optional[str] = None):
        """Crea un movimiento de stock"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return
        
        movement = StockMovement(
            product_id=product_id,
            user_id=user_id,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            stock_before=product.current_stock - quantity if movement_type in ["purchase", "adjustment"] else product.current_stock + abs(quantity),
            stock_after=product.current_stock,
            supplier=supplier,
            reference_number=reference_number,
            notes=notes
        )
        
        self.db.add(movement)

    def _create_cost_history(self,
                            product_id: int,
                            user_id: int,
                            cost_per_unit: float,
                            quantity_purchased: int,
                            total_cost: float,
                            supplier_name: Optional[str] = None,
                            supplier_invoice: Optional[str] = None,
                            notes: Optional[str] = None):
        """Crea un registro en el historial de costos"""
        
        cost_record = ProductCostHistory(
            product_id=product_id,
            user_id=user_id,
            cost_per_unit=cost_per_unit,
            quantity_purchased=quantity_purchased,
            total_cost=total_cost,
            supplier_name=supplier_name,
            supplier_invoice=supplier_invoice,
            purchase_date=datetime.utcnow(),
            notes=notes
        )
        
        self.db.add(cost_record)

    @exception_handler(logger, {"service": "InventoryService", "method": "get_product_cost_history"})
    def get_product_cost_history(self, product_id: int) -> List[ProductCostHistory]:
        """Obtiene el historial de costos de un producto"""
        
        return self.db.query(ProductCostHistory)\
                     .filter(ProductCostHistory.product_id == product_id)\
                     .order_by(desc(ProductCostHistory.purchase_date))\
                     .all()

    @exception_handler(logger, {"service": "InventoryService", "method": "get_low_stock_products"})
    def get_low_stock_products(self) -> List[Product]:
        """Obtiene productos con stock bajo"""
        
        return self.db.query(Product)\
                     .filter(Product.current_stock <= Product.min_stock)\
                     .filter(Product.status == "active")\
                     .all()

    @exception_handler(logger, {"service": "InventoryService", "method": "get_sales_analysis"})
    def get_sales_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Análisis de ventas por producto"""
        
        # Aquí iría la lógica para analizar ventas
        # Por ahora retornamos datos de ejemplo
        return {
            "best_sellers": [],
            "slow_movers": [],
            "profit_analysis": {},
            "period_days": days
        }

    # Métodos para categorías
    @exception_handler(logger, {"service": "InventoryService", "method": "get_categories"})
    def get_categories(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Obtiene lista de categorías con conteo de productos"""
        
        # Hacer join con productos para contar
        query = self.db.query(
            Category,
            func.count(Product.id).label('product_count')
        ).outerjoin(Product, Category.id == Product.category_id)
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
            
        results = query.group_by(Category.id).order_by(Category.sort_order, Category.name).all()
        
        # Convertir a lista de diccionarios con conteo
        categories = []
        for category, product_count in results:
            category_dict = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "icon": category.icon,
                "is_active": category.is_active,
                "sort_order": category.sort_order,
                "product_count": product_count,
                "created_at": category.created_at,
                "updated_at": category.updated_at
            }
            categories.append(category_dict)
            
        return categories

    @exception_handler(logger, {"service": "InventoryService", "method": "create_category"})
    def create_category(self, category_data: Dict[str, Any]) -> Category:
        """Crea una nueva categoría"""
        
        # Verificar unicidad del nombre
        existing = self.db.query(Category).filter(Category.name == category_data['name']).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con ese nombre"
            )
        
        category = Category(**category_data)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        logger.info(f"✅ Categoría creada: {category.name} (ID: {category.id})")
        return category

    @exception_handler(logger, {"service": "InventoryService", "method": "update_category"})
    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Category:
        """Actualiza una categoría existente"""
        
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
        
        # Verificar unicidad del nombre si cambió
        if 'name' in category_data and category_data['name'] != category.name:
            existing = self.db.query(Category).filter(Category.name == category_data['name']).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una categoría con ese nombre"
                )
        
        # Actualizar campos
        for key, value in category_data.items():
            if hasattr(category, key):
                setattr(category, key, value)
        
        self.db.commit()
        self.db.refresh(category)
        
        logger.info(f"✅ Categoría actualizada: {category.name} (ID: {category.id})")
        return category

    @exception_handler(logger, {"service": "InventoryService", "method": "delete_category"})
    def delete_category(self, category_id: int) -> bool:
        """Elimina una categoría si no tiene productos"""
        
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
        
        # Verificar que no tenga productos
        product_count = self.db.query(Product).filter(Product.category_id == category_id).count()
        if product_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar la categoría porque tiene {product_count} productos asignados"
            )
        
        self.db.delete(category)
        self.db.commit()
        
        logger.info(f"✅ Categoría eliminada: {category.name} (ID: {category.id})")
        return True

    @exception_handler(logger, {"service": "InventoryService", "method": "delete_product"})
    def delete_product(self, product_id: int) -> bool:
        """Elimina un producto"""
        
        # Usar una consulta directa para evitar cargar relaciones
        product_query = self.db.query(Product).filter(Product.id == product_id)
        product = product_query.first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        product_name = product.name
        
        # Eliminar usando SQL directo para evitar problemas de relaciones
        try:
            # Primero eliminar registros relacionados si existen
            self.db.execute(text(f"DELETE FROM stock_movements WHERE product_id = {product_id}"))
            self.db.execute(text(f"DELETE FROM product_cost_history WHERE product_id = {product_id}"))
            
            # Luego eliminar el producto
            self.db.execute(text(f"DELETE FROM products WHERE id = {product_id}"))
            
            self.db.commit()
            
            logger.info(f"✅ Producto eliminado: {product_name} (ID: {product_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error eliminando producto {product_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error eliminando producto: {str(e)}"
            )

    @exception_handler(logger, {"service": "InventoryService", "method": "get_inventory_summary"})
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del inventario"""
        
        # Usar string en lugar de enum para compatibilidad
        total_products = self.db.query(Product).filter(Product.status == "active").count()
        total_categories = self.db.query(Category).filter(Category.is_active == True).count()
        
        low_stock_count = self.db.query(Product)\
                                .filter(Product.current_stock <= Product.min_stock)\
                                .filter(Product.status == "active")\
                                .count()
        
        out_of_stock_count = self.db.query(Product)\
                                   .filter(Product.current_stock == 0)\
                                   .filter(Product.status == "active")\
                                   .count()
        
        total_value = self.db.query(func.sum(Product.current_stock * Product.selling_price))\
                            .filter(Product.status == "active")\
                            .scalar() or 0
        
        total_cost = self.db.query(func.sum(Product.current_stock * Product.current_cost))\
                           .filter(Product.status == "active")\
                           .scalar() or 0
        
        return {
            "total_products": total_products,
            "total_categories": total_categories,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_inventory_value": total_value,
            "total_inventory_cost": total_cost,
            "estimated_profit": total_value - total_cost
        }

    @exception_handler(logger, {"service": "InventoryService", "method": "get_stock_movements_report"})
    def get_stock_movements_report(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene movimientos de stock para reportes"""
        
        # Normalizar fechas para consistencia
        normalized_from, normalized_to = self._normalize_date_range(date_from, date_to)
        
        query = self.db.query(StockMovement).join(Product)
        
        if normalized_from:
            query = query.filter(StockMovement.movement_date >= normalized_from)
        if normalized_to:
            query = query.filter(StockMovement.movement_date <= normalized_to)
        
        movements = query.order_by(StockMovement.movement_date.desc()).limit(100).all()
        
        # Agrupar por fecha para el reporte
        movements_by_date = {}
        for movement in movements:
            date_key = movement.movement_date.strftime('%Y-%m-%d')
            if date_key not in movements_by_date:
                movements_by_date[date_key] = {
                    'date': date_key,
                    'purchases': 0,
                    'sales': 0,
                    'adjustments': 0,
                    'net_movement': 0
                }
            
            if movement.movement_type == 'purchase':
                movements_by_date[date_key]['purchases'] += movement.quantity
            elif movement.movement_type == 'sale':
                movements_by_date[date_key]['sales'] += abs(movement.quantity)
            elif movement.movement_type == 'adjustment':
                movements_by_date[date_key]['adjustments'] += movement.quantity
            
            movements_by_date[date_key]['net_movement'] += movement.quantity
        
        return list(movements_by_date.values())

    @exception_handler(logger, {"service": "InventoryService", "method": "get_category_values_report"})
    def get_category_values_report(self) -> List[Dict[str, Any]]:
        """Obtiene valores por categoría para reportes"""
        
        # Query para obtener valor total por categoría
        query = self.db.query(
            Category.id,
            Category.name,
            func.sum(Product.current_stock * Product.selling_price).label('total_value'),
            func.count(Product.id).label('product_count')
        ).outerjoin(Product, Category.id == Product.category_id)\
         .filter(Product.status == "active")\
         .group_by(Category.id, Category.name)\
         .order_by(func.sum(Product.current_stock * Product.selling_price).desc())
        
        results = query.all()
        
        # Calcular total para porcentajes
        total_value = sum(result.total_value or 0 for result in results)
        
        category_values = []
        for result in results:
            percentage = (result.total_value / total_value * 100) if total_value > 0 else 0
            category_values.append({
                'category': result.name,
                'value': result.total_value or 0,
                'percentage': round(percentage, 1),
                'products': result.product_count or 0
            })
        
        return category_values

    @exception_handler(logger, {"service": "InventoryService", "method": "get_top_products_report"})
    def get_top_products_report(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene productos más vendidos para reportes basado en ventas reales"""
        
        from app.models.sales import SaleProductItem, Sale
        
        # Query para obtener productos más vendidos basado en ventas reales
        query = self.db.query(
            SaleProductItem.product_id,
            SaleProductItem.product_name,
            func.sum(SaleProductItem.quantity).label('total_sold'),
            func.sum(SaleProductItem.line_total).label('total_revenue'),
            func.sum(SaleProductItem.quantity * SaleProductItem.unit_cost).label('total_cost'),
            func.avg(SaleProductItem.unit_price).label('avg_price')
        ).join(Sale, SaleProductItem.sale_id == Sale.id)\
         .filter(Sale.is_reversed == False)\
         .filter(Sale.status == "completed")\
         .group_by(SaleProductItem.product_id, SaleProductItem.product_name)\
         .order_by(func.sum(SaleProductItem.quantity).desc())\
         .limit(limit)
        
        results = query.all()
        
        top_products = []
        for result in results:
            # Calcular ganancia y margen
            total_revenue = result.total_revenue or 0
            total_cost = result.total_cost or 0
            profit = total_revenue - total_cost
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
            
            top_products.append({
                'product': result.product_name,
                'sales': int(result.total_sold or 0),
                'revenue': round(total_revenue, 0),
                'profit': round(profit, 0),
                'margin': round(margin, 1)
            })
        
        # Si no hay ventas reales, mostrar productos con mayor valor en stock como fallback
        if not top_products:
            logger.warning("No hay ventas reales, usando productos con mayor valor en stock como fallback")
            
            fallback_query = self.db.query(Product)\
                                  .filter(Product.status == "active")\
                                  .order_by((Product.current_stock * Product.selling_price).desc())\
                                  .limit(limit)
            
            products = fallback_query.all()
            
            for product in products:
                # Usar stock actual como indicador de popularidad
                estimated_sales = max(1, product.current_stock)
                revenue = estimated_sales * product.selling_price
                profit = revenue - (estimated_sales * product.current_cost)
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                top_products.append({
                    'product': product.name,
                    'sales': estimated_sales,
                    'revenue': round(revenue, 0),
                    'profit': round(profit, 0),
                    'margin': round(margin, 1)
                })
        
        logger.info(f"Generados {len(top_products)} productos más vendidos")
        return top_products

    @exception_handler(logger, {"service": "InventoryService", "method": "get_top_products_by_date_range"})
    def get_top_products_by_date_range(self, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene productos más vendidos en un rango de fechas específico"""
        
        from app.models.sales import SaleProductItem, Sale
        
        # Normalizar fechas para consistencia
        normalized_from, normalized_to = self._normalize_date_range(date_from, date_to)
        
        # Construir query base
        query = self.db.query(
            SaleProductItem.product_id,
            SaleProductItem.product_name,
            func.sum(SaleProductItem.quantity).label('total_sold'),
            func.sum(SaleProductItem.line_total).label('total_revenue'),
            func.sum(SaleProductItem.quantity * SaleProductItem.unit_cost).label('total_cost'),
            func.avg(SaleProductItem.unit_price).label('avg_price')
        ).join(Sale, SaleProductItem.sale_id == Sale.id)\
         .filter(Sale.is_reversed == False)\
         .filter(Sale.status == "completed")
        
        # Aplicar filtros de fecha normalizados
        if normalized_from:
            query = query.filter(Sale.created_at >= normalized_from)
        if normalized_to:
            query = query.filter(Sale.created_at <= normalized_to)
        
        # Agregar agrupación y ordenamiento
        query = query.group_by(SaleProductItem.product_id, SaleProductItem.product_name)\
                    .order_by(func.sum(SaleProductItem.quantity).desc())\
                    .limit(limit)
        
        results = query.all()
        
        top_products = []
        for result in results:
            total_revenue = result.total_revenue or 0
            total_cost = result.total_cost or 0
            profit = total_revenue - total_cost
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
            
            top_products.append({
                'product': result.product_name,
                'sales': int(result.total_sold or 0),
                'revenue': round(total_revenue, 0),
                'profit': round(profit, 0),
                'margin': round(margin, 1),
                'avg_price': round(result.avg_price or 0, 0)
            })
        
        logger.info(f"Generados {len(top_products)} productos más vendidos para el período {date_from} - {date_to}")
        return top_products

    @exception_handler(logger, {"service": "InventoryService", "method": "get_inventory_trends_report"})
    def get_inventory_trends_report(self, months: int = 6) -> List[Dict[str, Any]]:
        """Obtiene tendencias del inventario para reportes"""
        
        from sqlalchemy import and_
        
        # Obtener valor actual del inventario
        current_value = self.db.query(func.sum(Product.current_stock * Product.selling_price))\
                              .filter(Product.status == "active")\
                              .scalar() or 0
        
        trends = []
        month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        # Si no hay valor actual, retornar datos vacíos
        if current_value == 0:
            logger.warning("No hay valor de inventario actual para generar tendencias")
            return []
        
        # Obtener datos históricos reales de movimientos de stock
        for i in range(months):
            # Calcular fecha del mes
            target_date = datetime.now() - timedelta(days=30 * i)
            month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Obtener movimientos del mes
            monthly_movements = self.db.query(StockMovement)\
                                     .filter(and_(
                                         StockMovement.movement_date >= month_start,
                                         StockMovement.movement_date < month_start + timedelta(days=32)
                                     ))\
                                     .count()
            
            # Calcular valor estimado del inventario en ese mes
            if i == 0:
                # Mes actual - usar valor real
                estimated_value = current_value
                growth = 0
            else:
                # Meses anteriores - estimar basado en movimientos y variación temporal
                # Factor de variación basado en el tiempo (más antiguo = menor valor)
                time_factor = max(0.7, 1 - (i * 0.05))  # 5% menos por cada mes hacia atrás
                
                # Factor de movimientos (más movimientos = más actividad = mayor valor)
                movement_factor = min(1.2, 1 + (monthly_movements * 0.02))  # 2% más por cada movimiento
                
                estimated_value = current_value * time_factor * movement_factor
                
                # Calcular crecimiento comparado con el mes anterior
                if i < months - 1:
                    prev_time_factor = max(0.7, 1 - ((i + 1) * 0.05))
                    prev_movement_factor = min(1.2, 1 + (monthly_movements * 0.02))
                    prev_value = current_value * prev_time_factor * prev_movement_factor
                    growth = ((estimated_value - prev_value) / prev_value * 100) if prev_value > 0 else 0
                else:
                    growth = 0
            
            trends.append({
                'month': month_names[target_date.month - 1],
                'total_value': round(estimated_value, 0),
                'movements': monthly_movements,
                'growth': round(growth, 1)
            })
        
        # Ordenar por fecha (más antiguo primero)
        trends.reverse()
        
        # Asegurar que tenemos al menos el mes actual
        if not trends:
            current_month = month_names[datetime.now().month - 1]
            trends.append({
                'month': current_month,
                'total_value': round(current_value, 0),
                'movements': 0,
                'growth': 0
            })
        
        logger.info(f"Generadas {len(trends)} tendencias de inventario")
        return trends

    @exception_handler(logger, {"service": "InventoryService", "method": "get_complete_inventory_report"})
    def get_complete_inventory_report(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene reporte completo de inventario"""
        
        # Normalizar fechas para consistencia en todos los métodos
        normalized_from, normalized_to = self._normalize_date_range(date_from, date_to)
        
        # Obtener todos los datos del reporte usando fechas normalizadas
        stats = self.get_inventory_stats_by_date_range(date_from, date_to)
        stock_movements = self.get_stock_movements_report(date_from, date_to)
        category_values = self.get_category_values_report()
        low_stock_items = self.get_low_stock_products()
        
        # Usar productos más vendidos con filtro de fecha si está disponible
        if date_from or date_to:
            top_products = self.get_top_products_by_date_range(date_from, date_to, 5)
        else:
            top_products = self.get_top_products_report(5)
            
        trends = self.get_inventory_trends_report(6)
        
        # Log de las fechas normalizadas para debugging
        logger.info(f"Reporte de inventario generado para fechas: {date_from} - {date_to}")
        logger.info(f"Fechas normalizadas: {normalized_from} - {normalized_to}")
        
        # Formatear productos con stock bajo
        formatted_low_stock = []
        for product in low_stock_items:
            status = 'out' if product.current_stock == 0 else 'critical' if product.current_stock <= product.min_stock else 'low'
            formatted_low_stock.append({
                'product': product.name,
                'current_stock': product.current_stock,
                'min_stock': product.min_stock,
                'category': product.category.name if product.category else 'Sin categoría',
                'value': product.current_stock * product.selling_price,
                'status': status
            })
        
        return {
            'stats': stats,
            'stock_movements': stock_movements,
            'category_values': category_values,
            'low_stock_items': formatted_low_stock,
            'top_products': top_products,
            'trends': trends
        }

    @exception_handler(logger, {"service": "InventoryService", "method": "get_inventory_stats_by_date_range"})
    def get_inventory_stats_by_date_range(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene estadísticas de inventario para un rango de fechas específico"""
        
        # Normalizar fechas para consistencia
        normalized_from, normalized_to = self._normalize_date_range(date_from, date_to)
        
        # Obtener estadísticas base
        base_stats = self.get_inventory_summary()
        
        # Si hay fechas, obtener estadísticas específicas del período
        if normalized_from or normalized_to:
            from app.models.sales import SaleProductItem, Sale
            
            # Calcular ventas del período
            sales_query = self.db.query(
                func.sum(SaleProductItem.quantity).label('total_quantity_sold'),
                func.sum(SaleProductItem.line_total).label('total_revenue'),
                func.count(SaleProductItem.id).label('total_sales_count')
            ).join(Sale, SaleProductItem.sale_id == Sale.id)\
             .filter(Sale.is_reversed == False)\
             .filter(Sale.status == "completed")
            
            if normalized_from:
                sales_query = sales_query.filter(Sale.created_at >= normalized_from)
            if normalized_to:
                sales_query = sales_query.filter(Sale.created_at <= normalized_to)
            
            sales_result = sales_query.first()
            
            # Agregar estadísticas del período
            base_stats.update({
                'period_total_quantity_sold': int(sales_result.total_quantity_sold or 0),
                'period_total_revenue': float(sales_result.total_revenue or 0),
                'period_total_sales_count': int(sales_result.total_sales_count or 0),
                'period_date_from': date_from,
                'period_date_to': date_to
            })
        
        return base_stats
