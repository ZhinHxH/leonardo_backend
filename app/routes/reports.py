from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from pydantic import BaseModel, Field
import io
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.models.sales import Sale, SaleProductItem, SaleMembershipItem
from app.models.inventory import Product, Category
from app.models.clinical_history import MembershipPlan
from app.models.membership import Membership
from app.core.logging_config import main_logger

logger = main_logger
router = APIRouter(tags=["reports"])

# Schemas para respuestas
class RevenueByPlan(BaseModel):
    plan_name: str
    total_revenue: float
    sales_count: int
    average_ticket: float
    percentage: float

class PaymentMethodStats(BaseModel):
    method: str
    total_amount: float
    transaction_count: int
    percentage: float

class DailyRevenueTrend(BaseModel):
    date: str
    revenue: float
    transactions: int
    average_ticket: float

class RevenueSummary(BaseModel):
    total_revenue: float
    daily_average: float
    monthly_revenue: float
    total_transactions: int
    average_ticket: float
    growth_percentage: float

class RevenueReport(BaseModel):
    summary: RevenueSummary
    revenue_by_plan: List[RevenueByPlan]
    payment_methods: List[PaymentMethodStats]
    daily_trend: List[DailyRevenueTrend]
    top_products: List[Dict[str, Any]]
    membership_analytics: List[Dict[str, Any]]

@router.get("/revenue", response_model=RevenueReport)
async def get_revenue_report(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    seller_id: Optional[int] = Query(None, description="ID del vendedor"),
    payment_method: Optional[str] = Query(None, description="Método de pago"),
    membership_plan: Optional[str] = Query(None, description="Plan de membresía"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene reporte completo de ingresos con filtros avanzados
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha inválido para date_from"
                )
        
        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha inválido para date_to"
                )
        
        # Construir query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        # Aplicar filtros
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        if seller_id:
            query = query.filter(Sale.seller_id == seller_id)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        
        # Obtener datos básicos
        total_revenue = query.with_entities(func.sum(Sale.total_amount)).scalar() or 0
        total_transactions = query.count()
        average_ticket = total_revenue / total_transactions if total_transactions > 0 else 0
        
        logger.info(f"📊 Datos básicos obtenidos - Ingresos: {total_revenue}, Transacciones: {total_transactions}")
        
        # Calcular promedio diario
        if date_from_dt and date_to_dt:
            days_diff = (date_to_dt - date_from_dt).days
            daily_average = total_revenue / days_diff if days_diff > 0 else 0
        else:
            daily_average = 0
        
        # Obtener ingresos por plan
        try:
            revenue_by_plan = _get_revenue_by_plan(db, query, membership_plan)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo ingresos por plan: {e}")
            revenue_by_plan = []
        
        # Obtener distribución por método de pago
        try:
            payment_methods = _get_payment_methods_distribution(db, query)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo distribución de métodos de pago: {e}")
            payment_methods = []
        
        # Obtener tendencia diaria
        try:
            daily_trend = _get_daily_revenue_trend(db, query, date_from_dt, date_to_dt)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo tendencia diaria: {e}")
            daily_trend = []
        
        # Obtener productos más vendidos
        try:
            top_products = _get_top_products(db, query)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo productos más vendidos: {e}")
            top_products = []
        
        # Obtener análisis de membresías
        try:
            membership_analytics = _get_membership_analytics(db, query)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo análisis de membresías: {e}")
            membership_analytics = []
        
        # Calcular crecimiento (comparar con período anterior)
        growth_percentage = _calculate_growth_percentage(db, date_from_dt, date_to_dt)
        
        # Construir respuesta
        summary = RevenueSummary(
            total_revenue=total_revenue,
            daily_average=daily_average,
            monthly_revenue=total_revenue,  # Para el período seleccionado
            total_transactions=total_transactions,
            average_ticket=average_ticket,
            growth_percentage=growth_percentage
        )
        
        return RevenueReport(
            summary=summary,
            revenue_by_plan=revenue_by_plan,
            payment_methods=payment_methods,
            daily_trend=daily_trend,
            top_products=top_products,
            membership_analytics=membership_analytics
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo reporte de ingresos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/by-plan", response_model=List[RevenueByPlan])
async def get_revenue_by_plan(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene ingresos por plan de membresía"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        
        return _get_revenue_by_plan(db, query)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo ingresos por plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/payment-methods", response_model=List[PaymentMethodStats])
async def get_payment_methods_distribution(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene distribución por método de pago"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        
        return _get_payment_methods_distribution(db, query)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo distribución de métodos de pago: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/daily-trend", response_model=List[DailyRevenueTrend])
async def get_daily_revenue_trend(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene tendencia diaria de ingresos"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        
        return _get_daily_revenue_trend(db, query, date_from_dt, date_to_dt)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo tendencia diaria: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/top-products")
async def get_top_products(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limit: int = Query(10, description="Número de productos a retornar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene productos más vendidos"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        
        return _get_top_products(db, query, limit)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo productos más vendidos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/membership-analytics")
async def get_membership_analytics(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene análisis de membresías"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        
        return _get_membership_analytics(db, query)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo análisis de membresías: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/sold-items")
async def get_sold_items(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    seller_id: Optional[int] = Query(None, description="ID del vendedor"),
    payment_method: Optional[str] = Query(None, description="Método de pago"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(50, ge=1, le=200, description="Items por página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene lista detallada de items vendidos"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver reportes de ingresos"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base para ventas
        sales_query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            sales_query = sales_query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            sales_query = sales_query.filter(Sale.created_at <= date_to_dt)
        if seller_id:
            sales_query = sales_query.filter(Sale.seller_id == seller_id)
        if payment_method:
            sales_query = sales_query.filter(Sale.payment_method == payment_method)
        
        # Obtener IDs de ventas
        sale_ids = sales_query.with_entities(Sale.id).all()
        sale_id_list = [sale_id[0] for sale_id in sale_ids]
        
        if not sale_id_list:
            return {
                "items": [],
                "total_items": 0,
                "total_pages": 0,
                "current_page": page
            }
        
        # Obtener items de productos vendidos con JOIN a Sale para obtener la fecha y número de venta
        product_items = db.query(SaleProductItem, Sale.created_at, Sale.sale_number).join(
            Sale, SaleProductItem.sale_id == Sale.id
        ).filter(
            SaleProductItem.sale_id.in_(sale_id_list)
        ).with_entities(
            SaleProductItem.sale_id,
            SaleProductItem.product_name,
            SaleProductItem.product_sku,
            SaleProductItem.quantity,
            SaleProductItem.unit_price,
            SaleProductItem.discount_percentage,
            SaleProductItem.line_total,
            Sale.created_at,
            Sale.sale_number
        ).order_by(desc(Sale.created_at)).all()
        
        # Obtener items de membresías vendidas con JOIN a Sale para obtener la fecha y número de venta
        membership_items = db.query(SaleMembershipItem, Sale.created_at, Sale.sale_number).join(
            Sale, SaleMembershipItem.sale_id == Sale.id
        ).filter(
            SaleMembershipItem.sale_id.in_(sale_id_list)
        ).with_entities(
            SaleMembershipItem.sale_id,
            SaleMembershipItem.plan_name,
            SaleMembershipItem.plan_duration_days,
            SaleMembershipItem.plan_price,
            SaleMembershipItem.start_date,
            SaleMembershipItem.end_date,
            Sale.created_at,
            Sale.sale_number
        ).order_by(desc(Sale.created_at)).all()
        
        # Combinar y formatear items
        all_items = []
        
        logger.info(f"📊 Procesando {len(product_items)} productos y {len(membership_items)} membresías")
        
        # Agregar productos
        for item in product_items:
            # Calcular descuento real si no está en la base de datos
            discount_percentage = item.discount_percentage or 0.0
            
            # Si no hay descuento en la base de datos, calcular si hay diferencia entre precio unitario y total
            if discount_percentage == 0.0 and item.quantity > 0:
                expected_total = item.unit_price * item.quantity
                if expected_total > item.line_total:
                    discount_percentage = ((expected_total - item.line_total) / expected_total) * 100
                    logger.info(f"💰 Descuento calculado para {item.product_name}: {discount_percentage:.2f}%")
            
            # Log si hay descuento
            if discount_percentage > 0:
                logger.info(f"🏷️ Producto {item.product_name} tiene descuento: {discount_percentage:.2f}%")
            
            all_items.append({
                "type": "product",
                "sale_id": item.sale_id,
                "sale_number": item.sale_number,
                "name": item.product_name,
                "sku": item.product_sku,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount_percentage": round(discount_percentage, 2),
                "total_price": item.line_total,
                "date": item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "duration_days": None,
                "start_date": None,
                "end_date": None
            })
        
        # Agregar membresías
        for item in membership_items:
            all_items.append({
                "type": "membership",
                "sale_id": item.sale_id,
                "sale_number": item.sale_number,
                "name": item.plan_name,
                "sku": None,
                "quantity": 1,
                "unit_price": item.plan_price,
                "discount_percentage": 0,
                "total_price": item.plan_price,
                "date": item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "duration_days": item.plan_duration_days,
                "start_date": item.start_date.strftime('%Y-%m-%d') if item.start_date else None,
                "end_date": item.end_date.strftime('%Y-%m-%d') if item.end_date else None
            })
        
        # Ordenar por fecha descendente
        all_items.sort(key=lambda x: x['date'], reverse=True)
        
        # Paginación
        total_items = len(all_items)
        total_pages = (total_items + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_items = all_items[start_index:end_index]
        
        return {
            "items": paginated_items,
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo items vendidos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Funciones auxiliares
def _get_revenue_by_plan(db: Session, query, membership_plan: Optional[str] = None) -> List[RevenueByPlan]:
    """Obtiene ingresos por plan de membresía"""
    
    try:
        # Obtener ventas que tienen membresías
        sale_ids = query.with_entities(Sale.id).all()
        sale_id_list = [sale_id[0] for sale_id in sale_ids]
        
        if not sale_id_list:
            return []
        
        # Query para obtener membresías de esas ventas
        membership_query = db.query(SaleMembershipItem).filter(
            SaleMembershipItem.sale_id.in_(sale_id_list)
        )
        
        if membership_plan:
            membership_query = membership_query.filter(
                SaleMembershipItem.plan_name == membership_plan
            )
        
        # Agrupar por plan usando los datos de SaleMembershipItem
        plan_stats = membership_query.with_entities(
            SaleMembershipItem.plan_name,
            func.sum(SaleMembershipItem.plan_price).label('total_revenue'),
            func.count(SaleMembershipItem.id).label('sales_count')
        ).group_by(SaleMembershipItem.plan_name).all()
        
        # Calcular total para porcentajes
        total_revenue = sum(stat.total_revenue for stat in plan_stats)
        
        result = []
        for stat in plan_stats:
            percentage = (stat.total_revenue / total_revenue * 100) if total_revenue > 0 else 0
            average_ticket = stat.total_revenue / stat.sales_count if stat.sales_count > 0 else 0
            
            result.append(RevenueByPlan(
                plan_name=stat.plan_name,
                total_revenue=stat.total_revenue,
                sales_count=stat.sales_count,
                average_ticket=average_ticket,
                percentage=percentage
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en _get_revenue_by_plan: {e}")
        return []

def _get_payment_methods_distribution(db: Session, query) -> List[PaymentMethodStats]:
    """Obtiene distribución por método de pago"""
    
    # Agrupar por método de pago
    method_stats = query.with_entities(
        Sale.payment_method,
        func.sum(Sale.total_amount).label('total_amount'),
        func.count(Sale.id).label('transaction_count')
    ).group_by(Sale.payment_method).all()
    
    # Calcular total para porcentajes
    total_amount = sum(stat.total_amount for stat in method_stats)
    
    result = []
    for stat in method_stats:
        percentage = (stat.total_amount / total_amount * 100) if total_amount > 0 else 0
        
        result.append(PaymentMethodStats(
            method=stat.payment_method,
            total_amount=stat.total_amount,
            transaction_count=stat.transaction_count,
            percentage=percentage
        ))
    
    return result

def _get_daily_revenue_trend(db: Session, query, date_from_dt, date_to_dt) -> List[DailyRevenueTrend]:
    """Obtiene tendencia diaria de ingresos"""
    
    # Agrupar por día
    daily_stats = query.with_entities(
        func.date(Sale.created_at).label('date'),
        func.sum(Sale.total_amount).label('revenue'),
        func.count(Sale.id).label('transactions')
    ).group_by(func.date(Sale.created_at)).order_by('date').all()
    
    result = []
    for stat in daily_stats:
        average_ticket = stat.revenue / stat.transactions if stat.transactions > 0 else 0
        
        result.append(DailyRevenueTrend(
            date=stat.date.strftime('%Y-%m-%d'),
            revenue=stat.revenue,
            transactions=stat.transactions,
            average_ticket=average_ticket
        ))
    
    return result

def _get_top_products(db: Session, query, limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene productos más vendidos"""
    
    try:
        # Obtener ventas que tienen productos
        sale_ids = query.with_entities(Sale.id).all()
        sale_id_list = [sale_id[0] for sale_id in sale_ids]
        
        if not sale_id_list:
            return []
        
        # Query para obtener productos de esas ventas
        product_stats = db.query(SaleProductItem).filter(
            SaleProductItem.sale_id.in_(sale_id_list)
        ).with_entities(
            SaleProductItem.product_name,
            func.sum(SaleProductItem.quantity).label('sales_count'),
            func.sum(SaleProductItem.quantity * SaleProductItem.unit_price).label('revenue')
        ).group_by(SaleProductItem.product_name).order_by(
            desc('sales_count')
        ).limit(limit).all()
        
        result = []
        for stat in product_stats:
            result.append({
                'product_name': stat.product_name,
                'category': 'General',  # Por ahora categoría fija
                'sales_count': stat.sales_count,
                'revenue': stat.revenue
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en _get_top_products: {e}")
        return []

def _get_membership_analytics(db: Session, query) -> List[Dict[str, Any]]:
    """Obtiene análisis de membresías"""
    
    try:
        # Obtener ventas que tienen membresías
        sale_ids = query.with_entities(Sale.id).all()
        sale_id_list = [sale_id[0] for sale_id in sale_ids]
        
        if not sale_id_list:
            return []
        
        # Query para obtener membresías de esas ventas
        membership_stats = db.query(SaleMembershipItem).filter(
            SaleMembershipItem.sale_id.in_(sale_id_list)
        ).with_entities(
            SaleMembershipItem.plan_name,
            func.count(SaleMembershipItem.id).label('new_memberships'),
            func.sum(SaleMembershipItem.plan_price).label('revenue')
        ).group_by(SaleMembershipItem.plan_name).all()
        
        result = []
        for stat in membership_stats:
            result.append({
                'plan_name': stat.plan_name,
                'new_memberships': stat.new_memberships,
                'renewals': 0,  # TODO: Implementar lógica de renovaciones
                'revenue': stat.revenue
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en _get_membership_analytics: {e}")
        return []

def _calculate_growth_percentage(db: Session, date_from_dt, date_to_dt) -> float:
    """Calcula porcentaje de crecimiento comparado con período anterior"""
    
    if not date_from_dt or not date_to_dt:
        return 0.0
    
    # Calcular duración del período
    period_days = (date_to_dt - date_from_dt).days
    
    # Período anterior
    prev_date_from = date_from_dt - timedelta(days=period_days)
    prev_date_to = date_from_dt
    
    # Ingresos del período actual
    current_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.status == "completed",
        Sale.created_at >= date_from_dt,
        Sale.created_at < date_to_dt
    ).scalar() or 0
    
    # Ingresos del período anterior
    previous_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.status == "completed",
        Sale.created_at >= prev_date_from,
        Sale.created_at < prev_date_to
    ).scalar() or 0
    
    if previous_revenue == 0:
        return 100.0 if current_revenue > 0 else 0.0
    
    return ((current_revenue - previous_revenue) / previous_revenue) * 100

# Endpoints de exportación
@router.get("/revenue/export/pdf")
async def export_revenue_pdf(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    seller_id: Optional[int] = Query(None, description="ID del vendedor"),
    payment_method: Optional[str] = Query(None, description="Método de pago"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporta reporte de ingresos a PDF"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para exportar reportes"
        )
    
    try:
        # Obtener datos del reporte
        filters = {
            'date_from': date_from,
            'date_to': date_to,
            'seller_id': seller_id,
            'payment_method': payment_method
        }
        
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        if seller_id:
            query = query.filter(Sale.seller_id == seller_id)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        
        # Obtener datos
        total_revenue = query.with_entities(func.sum(Sale.total_amount)).scalar() or 0
        total_transactions = query.count()
        average_ticket = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph("REPORTE DE INGRESOS", title_style))
        story.append(Spacer(1, 20))
        
        # Información del período
        period_info = f"Período: {date_from or 'Inicio'} - {date_to or 'Fin'}"
        story.append(Paragraph(period_info, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Resumen
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total Ingresos', f"${total_revenue:,.0f}"],
            ['Total Transacciones', str(total_transactions)],
            ['Ticket Promedio', f"${average_ticket:,.0f}"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("RESUMEN EJECUTIVO", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detalles de ventas
        sales_data = query.order_by(desc(Sale.created_at)).limit(50).all()
        
        if sales_data:
            sales_table_data = [['Fecha', 'Número', 'Cliente', 'Total', 'Método']]
            for sale in sales_data:
                sales_table_data.append([
                    sale.created_at.strftime('%Y-%m-%d %H:%M'),
                    sale.sale_number,
                    sale.customer_id or 'N/A',
                    f"${sale.total_amount:,.0f}",
                    sale.payment_method
                ])
            
            sales_table = Table(sales_table_data)
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("DETALLES DE VENTAS (Últimas 50)", styles['Heading2']))
            story.append(sales_table)
        
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=reporte-ingresos-{datetime.now().strftime('%Y%m%d')}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"❌ Error exportando PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/revenue/export/excel")
async def export_revenue_excel(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    seller_id: Optional[int] = Query(None, description="ID del vendedor"),
    payment_method: Optional[str] = Query(None, description="Método de pago"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporta reporte de ingresos a Excel"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para exportar reportes"
        )
    
    try:
        # Convertir fechas
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        
        # Query base
        query = db.query(Sale).filter(Sale.status == "completed")
        
        if date_from_dt:
            query = query.filter(Sale.created_at >= date_from_dt)
        if date_to_dt:
            query = query.filter(Sale.created_at <= date_to_dt)
        if seller_id:
            query = query.filter(Sale.seller_id == seller_id)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        
        # Obtener datos de ventas
        sales_data = query.order_by(desc(Sale.created_at)).all()
        
        # Crear DataFrame
        sales_list = []
        for sale in sales_data:
            sales_list.append({
                'Fecha': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Número de Venta': sale.sale_number,
                'Cliente ID': sale.customer_id or 'N/A',
                'Vendedor ID': sale.seller_id,
                'Subtotal': sale.subtotal,
                'Descuento': sale.discount_amount,
                'Total': sale.total_amount,
                'Pagado': sale.amount_paid,
                'Cambio': sale.change_amount,
                'Método de Pago': sale.payment_method,
                'Estado': sale.status,
                'Notas': sale.notes or ''
            })
        
        df = pd.DataFrame(sales_list)
        
        # Crear Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen
            summary_data = {
                'Métrica': ['Total Ingresos', 'Total Transacciones', 'Ticket Promedio'],
                'Valor': [
                    df['Total'].sum(),
                    len(df),
                    df['Total'].mean() if len(df) > 0 else 0
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja de ventas detalladas
            df.to_excel(writer, sheet_name='Ventas Detalladas', index=False)
            
            # Hoja de análisis por método de pago
            payment_analysis = df.groupby('Método de Pago').agg({
                'Total': ['sum', 'count', 'mean'],
                'Fecha': 'count'
            }).round(2)
            payment_analysis.columns = ['Total Ingresos', 'Cantidad Transacciones', 'Ticket Promedio', 'Días']
            payment_analysis.to_excel(writer, sheet_name='Análisis por Método de Pago')
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=reporte-ingresos-{datetime.now().strftime('%Y%m%d')}.xlsx"}
        )
        
    except Exception as e:
        logger.error(f"❌ Error exportando Excel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )