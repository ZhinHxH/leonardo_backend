from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from fastapi import HTTPException, status
import json

from app.models.sales import Sale, SaleItem, MembershipSale, SaleReversalLog, SaleStatus, SaleType, PaymentMethod
from app.models.inventory import Product
from app.models.clinical_history import MembershipPlan
from app.models.membership import Membership, MembershipStatus
from app.models.user import User
from app.core.logging_config import main_logger, exception_handler

logger = main_logger

class SalesService:
    """Servicio para gestión completa de ventas"""
    
    def __init__(self, db: Session):
        self.db = db

    @exception_handler(logger, {"service": "SalesService", "method": "create_sale"})
    def create_sale(self, sale_data: Dict[str, Any], seller_id: int) -> Sale:
        """Crea una nueva venta completa"""
        
        # Generar número de venta único
        sale_number = self._generate_sale_number()
        
        # Calcular subtotal primero
        subtotal = 0.0
        
        # Procesar items de productos
        if 'products' in sale_data:
            for item_data in sale_data['products']:
                subtotal += self._calculate_product_subtotal(item_data)
        
        # Procesar membresías
        if 'memberships' in sale_data:
            logger.info(f"💳 Procesando {len(sale_data['memberships'])} membresías...")
            for membership_data in sale_data['memberships']:
                membership_subtotal = self._calculate_membership_subtotal(membership_data)
                subtotal += membership_subtotal
                logger.info(f"💳 Membresía calculada, subtotal parcial: {membership_subtotal}, subtotal total: {subtotal}")
        else:
            logger.info("💳 No hay membresías en la venta")
        
        # Calcular totales
        discount_amount = sale_data.get('discount_amount', 0.0)
        tax_amount = 0.0  # Sin IVA
        total_amount = subtotal - discount_amount
        
        logger.info(f"💰 Cálculo de totales - Subtotal: {subtotal}, Descuento: {discount_amount}, IVA: {tax_amount}, Total: {total_amount}")
        
        # Crear la venta principal con todos los totales calculados
        sale = Sale(
            sale_number=sale_number,
            customer_id=sale_data.get('customer_id'),
            seller_id=seller_id,
            sale_type=sale_data.get('sale_type', 'product'),
            payment_method=sale_data['payment_method'],
            amount_paid=sale_data['amount_paid'],
            notes=sale_data.get('notes'),
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            change_amount=sale_data['amount_paid'] - total_amount
        )
        
        self.db.add(sale)
        self.db.flush()  # Para obtener el ID
        
        logger.info(f"💳 Venta creada - Total: {sale.total_amount}, Pagado: {sale.amount_paid}, Cambio: {sale.change_amount}")
        
        # Ahora procesar los items reales
        # Procesar items de productos
        if 'products' in sale_data:
            for item_data in sale_data['products']:
                self._add_product_to_sale(sale.id, item_data)
        
        # Procesar membresías
        if 'memberships' in sale_data:
            for membership_data in sale_data['memberships']:
                self._add_membership_to_sale(sale.id, membership_data)
        
        # Validar pago
        if sale.amount_paid < total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pago insuficiente. Total: ${total_amount:,.0f}, Pagado: ${sale.amount_paid:,.0f}"
            )
        
        self.db.commit()
        self.db.refresh(sale)
        
        logger.info(f"✅ Venta creada: {sale.sale_number} - Total: ${sale.total_amount:,.0f}")
        return sale

    def _generate_sale_number(self) -> str:
        """Genera un número único de venta"""
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Contar ventas del día
        daily_count = self.db.query(Sale)\
                            .filter(func.date(Sale.created_at) == datetime.utcnow().date())\
                            .count()
        
        return f"VTA-{today}-{daily_count + 1:04d}"

    def _calculate_product_subtotal(self, item_data: Dict[str, Any]) -> float:
        """Calcula el subtotal de un producto sin crear el registro"""
        
        product = self.db.query(Product).filter(Product.id == item_data['product_id']).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto ID {item_data['product_id']} no encontrado"
            )
        
        quantity = item_data['quantity']
        
        # Verificar stock disponible
        if product.current_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {product.name}. Disponible: {product.current_stock}, Solicitado: {quantity}"
            )
        
        # Calcular total de línea
        unit_price = item_data.get('unit_price', product.selling_price)
        discount_percentage = item_data.get('discount_percentage', 0.0)
        line_total = quantity * unit_price * (1 - discount_percentage / 100)
        
        return line_total

    def _calculate_membership_subtotal(self, membership_data: Dict[str, Any]) -> float:
        """Calcula el subtotal de una membresía sin crear el registro"""
        
        plan = self.db.query(MembershipPlan).filter(MembershipPlan.id == membership_data['plan_id']).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan de membresía ID {membership_data['plan_id']} no encontrado"
            )
        
        customer_id = membership_data['customer_id']
        
        # Verificar que el cliente existe
        customer = self.db.query(User).filter(User.id == customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente ID {customer_id} no encontrado"
            )
        
        # Calcular precio del plan
        plan_price = plan.discount_price if plan.discount_price else plan.price
        logger.info(f"💳 Plan calculado: {plan.name}, Precio: {plan_price}")
        
        return plan_price

    def _add_product_to_sale(self, sale_id: int, item_data: Dict[str, Any]) -> float:
        """Agrega un producto a la venta y actualiza stock"""
        
        product = self.db.query(Product).filter(Product.id == item_data['product_id']).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto ID {item_data['product_id']} no encontrado"
            )
        
        quantity = item_data['quantity']
        
        # Verificar stock disponible
        if product.current_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {product.name}. Disponible: {product.current_stock}, Solicitado: {quantity}"
            )
        
        # Crear item de venta
        unit_price = item_data.get('unit_price', product.selling_price)
        discount_percentage = item_data.get('discount_percentage', 0.0)
        line_total = quantity * unit_price * (1 - discount_percentage / 100)
        
        sale_item = SaleItem(
            sale_id=sale_id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=product.current_cost,
            discount_percentage=discount_percentage,
            line_total=line_total
        )
        
        self.db.add(sale_item)
        
        # Actualizar stock del producto
        product.current_stock -= quantity
        product.last_sale_date = datetime.utcnow()
        
        # Crear movimiento de stock
        self._create_stock_movement(
            product_id=product.id,
            quantity=-quantity,  # Negativo para salida
            movement_type="sale",
            reference_number=f"Venta-{sale_id}",
            notes=f"Venta de {quantity} unidades"
        )
        
        return line_total

    def _add_membership_to_sale(self, sale_id: int, membership_data: Dict[str, Any]) -> float:
        """Agrega una membresía a la venta"""
        
        plan = self.db.query(MembershipPlan).filter(MembershipPlan.id == membership_data['plan_id']).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan de membresía ID {membership_data['plan_id']} no encontrado"
            )
        
        customer_id = membership_data['customer_id']
        
        # Verificar que el cliente existe
        customer = self.db.query(User).filter(User.id == customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente ID {customer_id} no encontrado"
            )
        
        # Calcular fechas de membresía
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=plan.duration_days)
        
        # Calcular precio del plan
        plan_price = plan.discount_price if plan.discount_price else plan.price
        logger.info(f"💳 Plan encontrado: {plan.name}, Precio original: {plan.price}, Precio con descuento: {plan.discount_price}, Precio final: {plan_price}")
        
        # Crear registro de venta de membresía
        membership_sale = MembershipSale(
            sale_id=sale_id,
            membership_plan_id=plan.id,
            plan_name=plan.name,
            plan_duration_days=plan.duration_days,
            plan_price=plan_price,
            membership_start_date=start_date,
            membership_end_date=end_date
        )
        
        self.db.add(membership_sale)
        self.db.flush()
        
        # Crear la membresía real
        membership = Membership(
            user_id=customer_id,
            type=plan.plan_type if plan.plan_type else "MONTHLY",  # Usar el tipo del plan o default
            start_date=start_date,
            end_date=end_date,
            price=membership_sale.plan_price,
            payment_method=membership_data.get('payment_method', 'cash'),
            is_active=True
        )
        
        self.db.add(membership)
        self.db.flush()
        
        logger.info(f"💳 Membresía agregada a venta - Plan: {plan.name}, Precio: {membership_sale.plan_price}")
        return membership_sale.plan_price

    def _create_stock_movement(self, product_id: int, quantity: int, movement_type: str, reference_number: str, notes: str):
        """Crea un movimiento de stock"""
        from app.models.inventory import StockMovement
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return
        
        movement = StockMovement(
            product_id=product_id,
            user_id=1,  # Sistema
            movement_type=movement_type,
            quantity=quantity,
            stock_before=product.current_stock - quantity if quantity < 0 else product.current_stock + quantity,
            stock_after=product.current_stock,
            reference_number=reference_number,
            notes=notes
        )
        
        self.db.add(movement)

    @exception_handler(logger, {"service": "SalesService", "method": "reverse_sale"})
    def reverse_sale(self, sale_id: int, reason: str, reversed_by_id: int) -> bool:
        """Reversa una venta completa"""
        
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada"
            )
        
        if not sale.can_be_reversed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta venta no puede ser reversada"
            )
        
        products_restocked = []
        memberships_cancelled = []
        
        try:
            # Reversar items de productos (reabastecer stock)
            for item in sale.items:
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    # Reabastecer stock
                    product.current_stock += item.quantity
                    
                    # Crear movimiento de stock de reversión
                    self._create_stock_movement(
                        product_id=product.id,
                        quantity=item.quantity,  # Positivo para entrada
                        movement_type="return",
                        reference_number=f"REV-{sale.sale_number}",
                        notes=f"Reversión de venta {sale.sale_number}"
                    )
                    
                    products_restocked.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": item.quantity
                    })
            
            # Reversar membresías (cancelar membresías activas)
            for membership_sale in sale.membership_sales:
                # Buscar membresías del cliente que coincidan con la venta
                memberships = self.db.query(Membership)\
                                   .filter(Membership.user_id == sale.customer_id)\
                                   .filter(Membership.is_active == True)\
                                   .filter(Membership.start_date >= sale.created_at)\
                                   .all()
                
                for membership in memberships:
                    membership.is_active = False
                    
                    memberships_cancelled.append({
                        "membership_id": membership.id,
                        "plan_name": membership_sale.plan_name,
                        "customer_id": membership.user_id
                    })
            
            # Marcar venta como reversada
            sale.is_reversed = True
            sale.reversed_by = reversed_by_id
            sale.reversed_at = datetime.utcnow()
            sale.reversal_reason = reason
            sale.status = "refunded"
            
            # Crear log de reversión
            reversal_log = SaleReversalLog(
                original_sale_id=sale.id,
                reversed_by=reversed_by_id,
                reason=reason,
                products_restocked=json.dumps(products_restocked),
                memberships_cancelled=json.dumps(memberships_cancelled),
                refunded_amount=sale.total_amount
            )
            
            self.db.add(reversal_log)
            self.db.commit()
            
            logger.info(f"✅ Venta reversada: {sale.sale_number} - ${sale.total_amount:,.0f}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error reversando venta {sale_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reversando venta: {str(e)}"
            )

    @exception_handler(logger, {"service": "SalesService", "method": "get_sales"})
    def get_sales(self, 
                 date_from: Optional[datetime] = None,
                 date_to: Optional[datetime] = None,
                 status: Optional[str] = None,
                 seller_id: Optional[int] = None,
                 page: int = 1,
                 per_page: int = 50) -> Dict[str, Any]:
        """Obtiene lista de ventas con filtros y paginación"""
        
        query = self.db.query(Sale).order_by(desc(Sale.created_at))
        
        # Aplicar filtros
        if date_from:
            query = query.filter(Sale.created_at >= date_from)
        if date_to:
            query = query.filter(Sale.created_at <= date_to)
        if status:
            query = query.filter(Sale.status == status)
        if seller_id:
            query = query.filter(Sale.seller_id == seller_id)
        
        # Contar total
        total_count = query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        sales = query.offset(offset).limit(per_page).all()
        
        # Calcular información de paginación
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            "sales": sales,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    @exception_handler(logger, {"service": "SalesService", "method": "get_products_for_sale"})
    def get_products_for_sale(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene productos disponibles para venta"""
        
        query = self.db.query(Product).filter(Product.status == "active")
        
        if search:
            query = query.filter(
                Product.name.ilike(f"%{search}%") |
                Product.barcode.ilike(f"%{search}%") |
                Product.sku.ilike(f"%{search}%")
            )
        
        products = query.order_by(Product.name).all()
        
        # Convertir a formato para POS
        products_data = []
        for product in products:
            products_data.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "sku": product.sku,
                "barcode": product.barcode,
                "price": product.selling_price,
                "stock": product.current_stock,
                "unit_of_measure": product.unit_of_measure,
                "category_name": getattr(product.category, 'name', 'Sin categoría') if product.category else 'Sin categoría',
                "is_available": product.current_stock > 0
            })
        
        return products_data

    # @exception_handler(logger, {"service": "SalesService", "method": "get_plans_for_sale"})
    # def get_plans_for_sale(self) -> List[MembershipPlan]:
    #     """Obtiene planes de membresía disponibles para venta"""
    #     
    #     return self.db.query(MembershipPlan)\
    #                  .filter(MembershipPlan.is_active == True)\
    #                  .order_by(MembershipPlan.sort_order, MembershipPlan.price)\
    #                  .all()

    @exception_handler(logger, {"service": "SalesService", "method": "get_sale_details"})
    def get_sale_details(self, sale_id: int) -> Dict[str, Any]:
        """Obtiene detalles completos de una venta"""
        
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada"
            )
        
        # Obtener items de productos
        product_items = []
        for item in sale.items:
            product_items.append({
                "id": item.id,
                "product_name": item.product_name,
                "product_sku": item.product_sku,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount_percentage": item.discount_percentage,
                "line_total": item.line_total
            })
        
        # Obtener membresías vendidas
        membership_items = []
        for membership_sale in sale.membership_sales:
            membership_items.append({
                "id": membership_sale.id,
                "plan_name": membership_sale.plan_name,
                "plan_price": membership_sale.plan_price,
                "duration_days": membership_sale.plan_duration_days,
                "start_date": membership_sale.membership_start_date,
                "end_date": membership_sale.membership_end_date
            })
        
        return {
            "sale": {
                "id": sale.id,
                "sale_number": sale.sale_number,
                "customer_id": sale.customer_id,
                "seller_id": sale.seller_id,
                "sale_type": sale.sale_type,
                "status": sale.status,
                "subtotal": sale.subtotal,
                "tax_amount": sale.tax_amount,
                "discount_amount": sale.discount_amount,
                "total_amount": sale.total_amount,
                "payment_method": sale.payment_method,
                "amount_paid": sale.amount_paid,
                "change_amount": sale.change_amount,
                "is_reversed": sale.is_reversed,
                "can_be_reversed": sale.can_be_reversed,
                "created_at": sale.created_at,
                "notes": sale.notes,
                "product_items": product_items,
                "membership_items": membership_items,
                "customer_name": sale.customer.name if sale.customer else "Cliente General",
                "seller_name": sale.seller.name if sale.seller else "Vendedor"
            }
        }

    @exception_handler(logger, {"service": "SalesService", "method": "get_sales_summary"})
    def get_sales_summary(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Obtiene resumen de ventas"""
        
        query = self.db.query(Sale).filter(Sale.status.in_(["completed", "refunded"]))
        
        if date_from:
            query = query.filter(Sale.created_at >= date_from)
        if date_to:
            query = query.filter(Sale.created_at <= date_to)
        
        # Calcular métricas
        total_sales = query.count()
        total_revenue = query.filter(Sale.status == "completed").with_entities(func.sum(Sale.total_amount)).scalar() or 0
        total_refunded = query.filter(Sale.status == "refunded").with_entities(func.sum(Sale.total_amount)).scalar() or 0
        
        # Ventas por método de pago
        payment_methods = self.db.query(
            Sale.payment_method,
            func.count(Sale.id).label('count'),
            func.sum(Sale.total_amount).label('total')
        ).filter(Sale.status == "completed")\
         .group_by(Sale.payment_method)\
         .all()
        
        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "total_refunded": total_refunded,
            "net_revenue": total_revenue - total_refunded,
            "payment_methods": [
                {
                    "method": pm[0],
                    "count": pm[1],
                    "total": pm[2]
                } for pm in payment_methods
            ]
        }

