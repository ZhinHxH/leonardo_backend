from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.logging_config import main_logger, exception_handler
from app.services.cash_closure_service import CashClosureService
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.cash_closure import (
    CashClosureCreate, CashClosureUpdate, CashClosureResponse, 
    CashClosureListResponse, CashClosureSummary, CashClosureReport
)

logger = main_logger
router = APIRouter(prefix="/cash-closures", tags=["cash-closures"])

@router.get("/shift-summary")
@exception_handler(logger, {"endpoint": "/cash-closures/shift-summary"})
async def get_shift_summary(
    shift_start: datetime = Query(..., description="Inicio del turno"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene resumen de ventas del turno actual"""
    
    # Solo usuarios con permisos pueden ver resúmenes de turno
    if current_user.role.upper() not in ["ADMIN", "MANAGER", "RECEPTIONIST"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver resúmenes de turno"
        )
    
    cash_closure_service = CashClosureService(db)
    summary = cash_closure_service.get_shift_sales_summary(
        user_id=current_user.id,
        shift_start=shift_start
    )
    
    return summary

@router.post("/", response_model=CashClosureResponse)
@exception_handler(logger, {"endpoint": "/cash-closures/create"})
async def create_cash_closure(
    cash_closure_data: CashClosureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuevo cierre de caja"""
    
    # Solo usuarios con permisos pueden crear cierres de caja
    if current_user.role.upper() not in ["ADMIN", "MANAGER", "RECEPTIONIST"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear cierres de caja"
        )
    
    cash_closure_service = CashClosureService(db)
    
    # Preparar datos de ventas
    sales_data = {
        'total_sales': cash_closure_data.total_sales,
        'total_products_sold': cash_closure_data.total_products_sold,
        'total_memberships_sold': cash_closure_data.total_memberships_sold,
        'total_daily_access_sold': cash_closure_data.total_daily_access_sold,
        'cash_sales': cash_closure_data.cash_sales,
        'nequi_sales': cash_closure_data.nequi_sales,
        'bancolombia_sales': cash_closure_data.bancolombia_sales,
        'daviplata_sales': cash_closure_data.daviplata_sales,
        'card_sales': cash_closure_data.card_sales,
        'transfer_sales': cash_closure_data.transfer_sales
    }
    
    # Preparar datos de conteo físico
    counted_data = {
        'cash_counted': cash_closure_data.cash_counted,
        'nequi_counted': cash_closure_data.nequi_counted,
        'bancolombia_counted': cash_closure_data.bancolombia_counted,
        'daviplata_counted': cash_closure_data.daviplata_counted,
        'card_counted': cash_closure_data.card_counted,
        'transfer_counted': cash_closure_data.transfer_counted
    }
    
    try:
        cash_closure = cash_closure_service.create_cash_closure(
            user_id=current_user.id,
            shift_start=cash_closure_data.shift_start,
            sales_data=sales_data,
            counted_data=counted_data,
            notes=cash_closure_data.notes
        )
        
        return cash_closure.to_dict()
        
    except Exception as e:
        logger.error(f"Error creando cierre de caja: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear cierre de caja"
        )

@router.get("/", response_model=CashClosureListResponse)
@exception_handler(logger, {"endpoint": "/cash-closures/list"})
async def get_cash_closures(
    user_id: Optional[int] = Query(None, description="ID del usuario"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    status: Optional[str] = Query(None, description="Estado del cierre"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(50, ge=1, le=500, description="Elementos por página"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene lista de cierres de caja con filtros"""
    
    # Solo administradores y gerentes pueden ver todos los cierres
    if current_user.role.upper() not in ["ADMIN", "MANAGER"]:
        # Los demás usuarios solo pueden ver sus propios cierres
        user_id = current_user.id
    
    cash_closure_service = CashClosureService(db)
    
    # Convertir status string a enum si se proporciona
    status_enum = None
    if status:
        try:
            from app.models.cash_closure import CashClosureStatus
            status_enum = CashClosureStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de cierre inválido"
            )
    
    result = cash_closure_service.get_cash_closures(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        status=status_enum,
        page=page,
        per_page=per_page
    )
    
    return result

@router.get("/{closure_id}", response_model=CashClosureResponse)
@exception_handler(logger, {"endpoint": "/cash-closures/get"})
async def get_cash_closure(
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene un cierre de caja específico"""
    
    cash_closure_service = CashClosureService(db)
    
    # Obtener el cierre de caja
    result = cash_closure_service.get_cash_closures(
        user_id=None,  # No filtrar por usuario aquí
        page=1,
        per_page=1
    )
    
    # Buscar el cierre específico
    closure = None
    for c in result['cash_closures']:
        if c['id'] == closure_id:
            closure = c
            break
    
    if not closure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cierre de caja no encontrado"
        )
    
    # Verificar permisos
    if (current_user.role.upper() not in ["ADMIN", "MANAGER"] and 
        closure['user_id'] != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este cierre de caja"
        )
    
    return closure

@router.put("/{closure_id}", response_model=CashClosureResponse)
@exception_handler(logger, {"endpoint": "/cash-closures/update"})
async def update_cash_closure(
    closure_id: int,
    update_data: CashClosureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza un cierre de caja"""
    
    # Solo administradores y gerentes pueden actualizar cierres
    if current_user.role.upper() not in ["ADMIN", "MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar cierres de caja"
        )
    
    cash_closure_service = CashClosureService(db)
    
    # Convertir a diccionario para la actualización
    update_dict = update_data.dict(exclude_unset=True)
    
    try:
        updated_closure = cash_closure_service.update_cash_closure(
            closure_id=closure_id,
            update_data=update_dict
        )
        
        return updated_closure.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando cierre de caja: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar cierre de caja"
        )

@router.get("/reports/summary", response_model=CashClosureReport)
@exception_handler(logger, {"endpoint": "/cash-closures/reports/summary"})
async def get_cash_closure_report(
    start_date: datetime = Query(..., description="Fecha de inicio del reporte"),
    end_date: datetime = Query(..., description="Fecha de fin del reporte"),
    user_id: Optional[int] = Query(None, description="ID del usuario específico"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Genera reporte de cierres de caja"""
    
    # Solo administradores y gerentes pueden generar reportes
    if current_user.role.upper() not in ["ADMIN", "MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para generar reportes de cierres de caja"
        )
    
    cash_closure_service = CashClosureService(db)
    
    try:
        report = cash_closure_service.get_cash_closure_report(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error generando reporte de cierres: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al generar reporte"
        )

@router.get("/reports/daily-summary")
@exception_handler(logger, {"endpoint": "/cash-closures/reports/daily-summary"})
async def get_daily_summary(
    date: datetime = Query(..., description="Fecha para el resumen diario"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene resumen diario de cierres de caja"""
    
    # Solo administradores y gerentes pueden ver resúmenes diarios
    if current_user.role.upper() not in ["ADMIN", "MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver resúmenes diarios"
        )
    
    cash_closure_service = CashClosureService(db)
    
    # Obtener cierres del día
    result = cash_closure_service.get_cash_closures(
        start_date=date,
        end_date=date,
        page=1,
        per_page=1000  # Obtener todos los cierres del día
    )
    
    # Calcular estadísticas del día
    closures = result['cash_closures']
    total_sales = sum(c['total_sales'] for c in closures)
    total_counted = sum(c['total_counted'] for c in closures)
    total_differences = sum(c['total_differences'] for c in closures)
    discrepancies_count = sum(1 for c in closures if c['has_discrepancies'])
    
    return {
        'date': date.date(),
        'total_closures': len(closures),
        'total_sales': total_sales,
        'total_counted': total_counted,
        'total_differences': total_differences,
        'discrepancies_count': discrepancies_count,
        'average_difference': total_differences / len(closures) if closures else 0.0,
        'closures': closures
    }
