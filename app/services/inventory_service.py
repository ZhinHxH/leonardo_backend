from datetime import datetime
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
