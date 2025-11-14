from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from fastapi import HTTPException, status

from app.models.cash_closure import CashClosure, CashClosureStatus
from app.models.sales import Sale
from app.models.user import User
from app.core.logging_config import main_logger, exception_handler

logger = main_logger

class CashClosureService:
    """Servicio para gestión de cierres de caja"""
    
    def __init__(self, db: Session):
        self.db = db

    @exception_handler(logger, {"service": "CashClosureService", "method": "create_cash_closure"})
    def create_cash_closure(self, user_id: int, shift_start: datetime, 
                          sales_data: Dict[str, Any], counted_data: Dict[str, Any],
                          notes: Optional[str] = None) -> CashClosure:
        """Crea un nuevo cierre de caja o actualiza uno existente para el mismo día"""
        
        # Validar que el cierre sea para una fecha reciente (no más de 1 día en el futuro)
        today = datetime.utcnow().date()
        shift_date = shift_start.date()
        
        # Permitir cierres para hoy o hasta 1 día en el futuro
        if shift_date > today + timedelta(days=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Los cierres de caja no pueden realizarse para fechas futuras. Fecha solicitada: {shift_date}, Fecha máxima permitida: {today + timedelta(days=1)}"
            )
        
        # Permitir cierres para fechas pasadas recientes (hasta 7 días atrás)
        if shift_date < today - timedelta(days=7):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Los cierres de caja no pueden realizarse para fechas muy antiguas. Fecha solicitada: {shift_date}, Fecha mínima permitida: {today - timedelta(days=7)}"
            )
        
        # Verificar si ya existe un cierre para este usuario en la fecha del turno
        logger.info(f"Buscando cierres existentes para usuario {user_id} en fecha {shift_date}")
        
        # Buscar cierres existentes para el usuario en la fecha del turno
        existing_closure = self.db.query(CashClosure)\
                                 .filter(CashClosure.user_id == user_id)\
                                 .filter(CashClosure.shift_date == shift_date)\
                                 .first()
        
        # Si no se encuentra, buscar en un rango de fechas cercanas (por si hay problemas de timezone)
        if not existing_closure:
            logger.info(f"No se encontró cierre exacto, buscando en rango de fechas cercanas")
            start_date = shift_date - timedelta(days=1)
            end_date = shift_date + timedelta(days=1)
            
            existing_closure = self.db.query(CashClosure)\
                                     .filter(CashClosure.user_id == user_id)\
                                     .filter(CashClosure.shift_date >= start_date)\
                                     .filter(CashClosure.shift_date <= end_date)\
                                     .first()
        
        if existing_closure:
            logger.info(f"Encontrado cierre existente {existing_closure.id} para usuario {user_id} en fecha {existing_closure.shift_date}")
            return self._update_existing_closure(existing_closure, shift_start, sales_data, counted_data, notes)
        else:
            logger.info(f"No se encontró cierre existente para usuario {user_id} en fecha {shift_date}, creando nuevo cierre")
        
        # Calcular diferencias
        differences = self._calculate_differences(sales_data, counted_data)
        
        # Crear el cierre de caja
        cash_closure = CashClosure(
            user_id=user_id,
            shift_date=shift_date,
            shift_start=shift_start,
            shift_end=datetime.utcnow(),
            total_sales=sales_data.get('total_sales', 0.0),
            total_products_sold=sales_data.get('total_products_sold', 0),
            total_memberships_sold=sales_data.get('total_memberships_sold', 0),
            total_daily_access_sold=sales_data.get('total_daily_access_sold', 0),
            cash_sales=sales_data.get('cash_sales', 0.0),
            nequi_sales=sales_data.get('nequi_sales', 0.0),
            bancolombia_sales=sales_data.get('bancolombia_sales', 0.0),
            daviplata_sales=sales_data.get('daviplata_sales', 0.0),
            card_sales=sales_data.get('card_sales', 0.0),
            transfer_sales=sales_data.get('transfer_sales', 0.0),
            cash_counted=counted_data.get('cash_counted', 0.0),
            nequi_counted=counted_data.get('nequi_counted', 0.0),
            bancolombia_counted=counted_data.get('bancolombia_counted', 0.0),
            daviplata_counted=counted_data.get('daviplata_counted', 0.0),
            card_counted=counted_data.get('card_counted', 0.0),
            transfer_counted=counted_data.get('transfer_counted', 0.0),
            cash_difference=differences.get('cash_difference', 0.0),
            nequi_difference=differences.get('nequi_difference', 0.0),
            bancolombia_difference=differences.get('bancolombia_difference', 0.0),
            daviplata_difference=differences.get('daviplata_difference', 0.0),
            card_difference=differences.get('card_difference', 0.0),
            transfer_difference=differences.get('transfer_difference', 0.0),
            notes=notes,
            discrepancies_notes=differences.get('discrepancies_notes'),
            status=CashClosureStatus.PENDING
        )
        
        self.db.add(cash_closure)
        self.db.commit()
        self.db.refresh(cash_closure)
        
        return cash_closure

    @exception_handler(logger, {"service": "CashClosureService", "method": "get_today_closure"})
    def get_today_closure(self, user_id: int) -> Optional[CashClosure]:
        """Obtiene el cierre de caja del día actual para un usuario"""
        
        today = datetime.utcnow().date()
        closure = self.db.query(CashClosure)\
                        .filter(CashClosure.user_id == user_id)\
                        .filter(CashClosure.shift_date == today)\
                        .first()
        
        return closure

    @exception_handler(logger, {"service": "CashClosureService", "method": "get_cash_closure_by_id"})
    def get_cash_closure_by_id(self, closure_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un cierre de caja por ID con información del usuario"""
        
        closure = self.db.query(CashClosure, User.name.label('user_name'))\
                        .join(User, CashClosure.user_id == User.id)\
                        .filter(CashClosure.id == closure_id)\
                        .first()
        
        if not closure:
            return None
        
        closure_obj, user_name = closure
        closure_dict = closure_obj.to_dict()
        closure_dict['user_name'] = user_name
        
        return closure_dict

    def _update_existing_closure(self, existing_closure: CashClosure, shift_start: datetime,
                               sales_data: Dict[str, Any], counted_data: Dict[str, Any],
                               notes: Optional[str] = None) -> CashClosure:
        """Actualiza un cierre de caja existente recalculando las ventas desde el inicio del turno"""
        
        # Recalcular ventas desde el inicio del turno para incluir nuevas ventas
        logger.info(f"Recalculando ventas para cierre existente {existing_closure.id} desde {shift_start}")
        updated_sales_data = self.get_shift_sales_summary(existing_closure.user_id, shift_start)
        
        # Usar los datos recalculados en lugar de los datos enviados
        sales_data = updated_sales_data
        
        # Calcular diferencias con los datos actualizados
        differences = self._calculate_differences(sales_data, counted_data)
        
        # Actualizar campos de ventas con datos recalculados
        existing_closure.total_sales = sales_data.get('total_sales', 0.0)
        existing_closure.total_products_sold = sales_data.get('total_products_sold', 0)
        existing_closure.total_memberships_sold = sales_data.get('total_memberships_sold', 0)
        existing_closure.total_daily_access_sold = sales_data.get('total_daily_access_sold', 0)
        
        # Actualizar desglose por método de pago con datos recalculados
        existing_closure.cash_sales = sales_data.get('cash_sales', 0.0)
        existing_closure.nequi_sales = sales_data.get('nequi_sales', 0.0)
        existing_closure.bancolombia_sales = sales_data.get('bancolombia_sales', 0.0)
        existing_closure.daviplata_sales = sales_data.get('daviplata_sales', 0.0)
        existing_closure.card_sales = sales_data.get('card_sales', 0.0)
        existing_closure.transfer_sales = sales_data.get('transfer_sales', 0.0)
        
        # Actualizar conteo físico
        existing_closure.cash_counted = counted_data.get('cash_counted', 0.0)
        existing_closure.nequi_counted = counted_data.get('nequi_counted', 0.0)
        existing_closure.bancolombia_counted = counted_data.get('bancolombia_counted', 0.0)
        existing_closure.daviplata_counted = counted_data.get('daviplata_counted', 0.0)
        existing_closure.card_counted = counted_data.get('card_counted', 0.0)
        existing_closure.transfer_counted = counted_data.get('transfer_counted', 0.0)
        
        # Actualizar diferencias
        existing_closure.cash_difference = differences.get('cash_difference', 0.0)
        existing_closure.nequi_difference = differences.get('nequi_difference', 0.0)
        existing_closure.bancolombia_difference = differences.get('bancolombia_difference', 0.0)
        existing_closure.daviplata_difference = differences.get('daviplata_difference', 0.0)
        existing_closure.card_difference = differences.get('card_difference', 0.0)
        existing_closure.transfer_difference = differences.get('transfer_difference', 0.0)
        
        # Actualizar notas y timestamps
        if notes:
            existing_closure.notes = notes
        existing_closure.shift_end = datetime.utcnow()
        existing_closure.discrepancies_notes = differences.get('discrepancies_notes')
        
        # Marcar como actualizado
        existing_closure.status = CashClosureStatus.PENDING
        
        self.db.commit()
        self.db.refresh(existing_closure)
        
        logger.info(f"Cierre de caja {existing_closure.id} actualizado exitosamente")
        return existing_closure

    def _calculate_differences(self, sales_data: Dict[str, Any], counted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula las diferencias entre ventas del sistema y conteo físico"""
        differences = {}
        discrepancies_notes = []
        
        payment_methods = ['cash', 'nequi', 'bancolombia', 'daviplata', 'card', 'transfer']
        
        for method in payment_methods:
            sales_key = f"{method}_sales"
            counted_key = f"{method}_counted"
            difference_key = f"{method}_difference"
            
            sales_amount = sales_data.get(sales_key, 0.0)
            counted_amount = counted_data.get(counted_key, 0.0)
            difference = counted_amount - sales_amount
            
            differences[difference_key] = difference
            
            # Si hay diferencia significativa, agregar nota
            if abs(difference) > 0.01:  # Tolerancia de 1 centavo
                discrepancies_notes.append(
                    f"{method.upper()}: Sistema ${sales_amount:.2f} vs Físico ${counted_amount:.2f} "
                    f"(Diferencia: ${difference:+.2f})"
                )
        
        if discrepancies_notes:
            differences['discrepancies_notes'] = "; ".join(discrepancies_notes)
        
        return differences

    @exception_handler(logger, {"service": "CashClosureService", "method": "get_cash_closures"})
    def get_cash_closures(self, 
                         user_id: Optional[int] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         status: Optional[CashClosureStatus] = None,
                         page: int = 1,
                         per_page: int = 50) -> Dict[str, Any]:
        """Obtiene lista de cierres de caja con filtros"""
        
        query = self.db.query(CashClosure, User.name.label('user_name'))\
                      .join(User, CashClosure.user_id == User.id)
        
        if user_id:
            query = query.filter(CashClosure.user_id == user_id)
            
        if start_date:
            query = query.filter(CashClosure.shift_date >= start_date.date())
            
        if end_date:
            query = query.filter(CashClosure.shift_date <= end_date.date())
            
        if status:
            query = query.filter(CashClosure.status == status)
        
        # Contar total
        total_query = self.db.query(CashClosure)
        if user_id:
            total_query = total_query.filter(CashClosure.user_id == user_id)
        if start_date:
            total_query = total_query.filter(CashClosure.shift_date >= start_date.date())
        if end_date:
            total_query = total_query.filter(CashClosure.shift_date <= end_date.date())
        if status:
            total_query = total_query.filter(CashClosure.status == status)
            
        total_count = total_query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        results = query.order_by(desc(CashClosure.created_at))\
                      .offset(offset).limit(per_page).all()
        
        # Convertir a lista de diccionarios
        cash_closures = []
        for closure, user_name in results:
            closure_dict = closure.to_dict()
            closure_dict['user_name'] = user_name
            cash_closures.append(closure_dict)
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            "cash_closures": cash_closures,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    @exception_handler(logger, {"service": "CashClosureService", "method": "get_shift_sales_summary"})
    def get_shift_sales_summary(self, user_id: int, shift_start: datetime) -> Dict[str, Any]:
        """Obtiene resumen de ventas del turno actual"""
        
        # Obtener ventas del turno (del usuario específico)
        sales_query = self.db.query(Sale)\
                           .filter(Sale.seller_id == user_id)\
                           .filter(Sale.created_at >= shift_start)\
                           .filter(Sale.status == "completed")  # Solo ventas completadas
        
        sales = sales_query.all()
        
        logger.info(f"Encontradas {len(sales)} ventas para el usuario {user_id} desde {shift_start}")
        
        # Calcular resúmenes
        total_sales = sum(sale.total_amount for sale in sales)
        total_products_sold = 0
        total_memberships_sold = 0
        total_daily_access_sold = 0
        
        # Desglose por método de pago
        payment_breakdown = {
            'cash': 0.0,
            'nequi': 0.0,
            'bancolombia': 0.0,
            'daviplata': 0.0,
            'card': 0.0,
            'transfer': 0.0
        }
        
        for sale in sales:
            logger.info(f"Procesando venta {sale.id}: tipo={sale.sale_type}, método={sale.payment_method}, monto={sale.total_amount}")
            
            # Contar por tipo de venta
            if sale.sale_type == "product":
                total_products_sold += 1
            elif sale.sale_type == "membership":
                total_memberships_sold += 1
            elif sale.sale_type == "mixed":
                # Para ventas mixtas, contar como producto y membresía
                total_products_sold += 1
                total_memberships_sold += 1
            
            # Desglose por método de pago
            payment_method = sale.payment_method.lower()
            if payment_method in payment_breakdown:
                payment_breakdown[payment_method] += sale.total_amount
            else:
                logger.warning(f"Método de pago no reconocido: {payment_method}")
        
        result = {
            'total_sales': total_sales,
            'total_products_sold': total_products_sold,
            'total_memberships_sold': total_memberships_sold,
            'total_daily_access_sold': total_daily_access_sold,
            'cash_sales': payment_breakdown['cash'],
            'nequi_sales': payment_breakdown['nequi'],
            'bancolombia_sales': payment_breakdown['bancolombia'],
            'daviplata_sales': payment_breakdown['daviplata'],
            'card_sales': payment_breakdown['card'],
            'transfer_sales': payment_breakdown['transfer'],
            'sales_count': len(sales)
        }
        
        logger.info(f"Resumen del turno generado: {result}")
        return result

    @exception_handler(logger, {"service": "CashClosureService", "method": "get_shift_items_sold"})
    def get_shift_items_sold(self, user_id: int, shift_start: datetime) -> Dict[str, Any]:
        """Obtiene el desglose de items vendidos en el turno con stock restante"""
        
        from app.models.sales import SaleProductItem
        from app.models.product import Product
        
        # Obtener ventas del turno (del usuario específico)
        sales_query = self.db.query(Sale)\
                           .filter(Sale.seller_id == user_id)\
                           .filter(Sale.created_at >= shift_start)\
                           .filter(Sale.status == "completed")  # Solo ventas completadas
        
        sales = sales_query.all()
        sale_ids = [sale.id for sale in sales]
        
        logger.info(f"Obteniendo items vendidos para {len(sale_ids)} ventas del usuario {user_id}")
        
        if not sale_ids:
            return {
                'items_sold': [],
                'total_items_sold': 0,
                'total_products_sold': 0
            }
        
        # Obtener items vendidos con información del producto
        items_query = self.db.query(
            SaleProductItem.product_id,
            Product.name.label('product_name'),
            Product.current_stock.label('remaining_stock'),
            Product.selling_price.label('unit_price'),
            SaleProductItem.quantity.label('quantity_sold')
        ).join(Product, SaleProductItem.product_id == Product.id)\
         .filter(SaleProductItem.sale_id.in_(sale_ids))
        
        items = items_query.all()
        
        # Agrupar por producto para sumar cantidades
        items_summary = {}
        for item in items:
            product_id = item.product_id
            if product_id not in items_summary:
                items_summary[product_id] = {
                    'product_id': product_id,
                    'product_name': item.product_name,
                    'remaining_stock': item.remaining_stock,
                    'unit_price': item.unit_price,
                    'quantity_sold': 0
                }
            items_summary[product_id]['quantity_sold'] += item.quantity_sold
        
        # Convertir a lista
        items_list = list(items_summary.values())
        
        # Calcular totales
        total_items_sold = sum(item['quantity_sold'] for item in items_list)
        total_products_sold = len(items_list)
        
        result = {
            'items_sold': items_list,
            'total_items_sold': total_items_sold,
            'total_products_sold': total_products_sold
        }
        
        logger.info(f"Desglose de items generado: {total_products_sold} productos únicos, {total_items_sold} items totales")
        return result

    @exception_handler(logger, {"service": "CashClosureService", "method": "update_cash_closure"})
    def update_cash_closure(self, closure_id: int, update_data: Dict[str, Any]) -> CashClosure:
        """Actualiza un cierre de caja"""
        
        closure = self.db.query(CashClosure).filter(CashClosure.id == closure_id).first()
        if not closure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cierre de caja no encontrado"
            )
        
        # Actualizar campos
        for field, value in update_data.items():
            if hasattr(closure, field) and value is not None:
                setattr(closure, field, value)
        
        # Si se está marcando como revisado, actualizar timestamps
        if update_data.get('status') == CashClosureStatus.REVIEWED:
            closure.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(closure)
        
        return closure

    @exception_handler(logger, {"service": "CashClosureService", "method": "get_cash_closure_report"})
    def get_cash_closure_report(self, 
                               start_date: datetime, 
                               end_date: datetime,
                               user_id: Optional[int] = None) -> Dict[str, Any]:
        """Genera reporte de cierres de caja"""
        
        query = self.db.query(CashClosure, User.name.label('user_name'))\
                      .join(User, CashClosure.user_id == User.id)\
                      .filter(CashClosure.shift_date >= start_date.date())\
                      .filter(CashClosure.shift_date <= end_date.date())
        
        if user_id:
            query = query.filter(CashClosure.user_id == user_id)
        
        closures = query.order_by(desc(CashClosure.shift_date)).all()
        
        # Calcular estadísticas
        total_closures = len(closures)
        total_sales = sum(closure.total_sales for closure, _ in closures)
        total_counted = sum(closure.total_counted for closure, _ in closures)
        total_differences = sum(closure.total_differences for closure, _ in closures)
        closures_with_discrepancies = sum(1 for closure, _ in closures if closure.has_discrepancies)
        
        # Resumen por usuario
        user_summary = {}
        for closure, user_name in closures:
            if user_name not in user_summary:
                user_summary[user_name] = {
                    'closures_count': 0,
                    'total_sales': 0.0,
                    'total_differences': 0.0,
                    'discrepancies_count': 0
                }
            
            user_summary[user_name]['closures_count'] += 1
            user_summary[user_name]['total_sales'] += closure.total_sales
            user_summary[user_name]['total_differences'] += closure.total_differences
            if closure.has_discrepancies:
                user_summary[user_name]['discrepancies_count'] += 1
        
        # Resumen diario
        daily_summary = {}
        for closure, user_name in closures:
            date_key = closure.shift_date.strftime('%Y-%m-%d')
            if date_key not in daily_summary:
                daily_summary[date_key] = {
                    'date': closure.shift_date,
                    'closures_count': 0,
                    'total_sales': 0.0,
                    'total_differences': 0.0,
                    'discrepancies_count': 0
                }
            
            daily_summary[date_key]['closures_count'] += 1
            daily_summary[date_key]['total_sales'] += closure.total_sales
            daily_summary[date_key]['total_differences'] += closure.total_differences
            if closure.has_discrepancies:
                daily_summary[date_key]['discrepancies_count'] += 1
        
        return {
            'period_start': start_date,
            'period_end': end_date,
            'total_closures': total_closures,
            'total_sales': total_sales,
            'total_counted': total_counted,
            'total_differences': total_differences,
            'closures_with_discrepancies': closures_with_discrepancies,
            'average_difference': total_differences / total_closures if total_closures > 0 else 0.0,
            'closures_by_user': [
                {
                    'user_name': user_name,
                    **stats
                } for user_name, stats in user_summary.items()
            ],
            'daily_summary': [
                {
                    'date': data['date'],
                    **{k: v for k, v in data.items() if k != 'date'}
                } for data in daily_summary.values()
            ]
        }
