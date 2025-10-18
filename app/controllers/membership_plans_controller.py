from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.logging_config import main_logger, exception_handler
from app.services.membership_service import MembershipService
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.models.clinical_history import MembershipPlan
from app.schemas.membership_plans import (
    MembershipPlanCreate, MembershipPlanUpdate, MembershipPlanResponse,
    AccessValidationResponse, PurchasePlanRequest
)

logger = main_logger
router = APIRouter(tags=["membership-plans"])

# Los schemas ahora están importados desde app.schemas.membership_plans

@router.get("/", response_model=List[MembershipPlanResponse])
@exception_handler(logger, {"endpoint": "/membership-plans/"})
async def get_plans(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene lista de planes de membresía"""
    
    membership_service = MembershipService(db)
    plans = membership_service.get_plans(include_inactive)
    
    return plans

@router.post("/", response_model=MembershipPlanResponse)
@exception_handler(logger, {"endpoint": "/membership-plans/", "method": "POST"})
async def create_plan(
    plan_data: MembershipPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuevo plan (solo administradores)"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y gerentes pueden crear planes"
        )
    
    membership_service = MembershipService(db)
    plan = membership_service.create_plan(plan_data.dict())
    
    return plan

@router.put("/{plan_id}", response_model=MembershipPlanResponse)
@exception_handler(logger, {"endpoint": "/membership-plans/{plan_id}", "method": "PUT"})
async def update_plan(
    plan_id: int,
    plan_data: MembershipPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza un plan (solo administradores)"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y gerentes pueden editar planes"
        )
    
    membership_service = MembershipService(db)
    plan = membership_service.update_plan(
        plan_id,
        plan_data.dict(exclude_unset=True)
    )
    
    return plan

@router.delete("/{plan_id}")
@exception_handler(logger, {"endpoint": "/membership-plans/{plan_id}", "method": "DELETE"})
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un plan (solo administradores)"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y gerentes pueden eliminar planes"
        )
    
    membership_service = MembershipService(db)
    success = membership_service.delete_plan(plan_id)
    
    return {"success": success, "message": "Plan eliminado exitosamente"}

@router.get("/active", response_model=List[MembershipPlanResponse])
@exception_handler(logger, {"endpoint": "/membership-plans/active"})
async def get_active_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene planes activos para ventas"""
    
    membership_service = MembershipService(db)
    plans = membership_service.get_active_plans_for_sale()
    
    return plans

@router.post("/validate-access/{user_id}", response_model=AccessValidationResponse)
@exception_handler(logger, {"endpoint": "/membership-plans/validate-access/{user_id}"})
async def validate_user_access(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Valida si un usuario tiene acceso válido"""
    
    # Solo personal autorizado puede validar acceso
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para validar acceso"
        )
    
    membership_service = MembershipService(db)
    access_info = membership_service.validate_user_access(user_id)
    
    return access_info

@router.post("/purchase/{plan_id}")
@exception_handler(logger, {"endpoint": "/membership-plans/purchase/{plan_id}"})
async def purchase_plan(
    plan_id: int,
    user_id: int,
    payment_method: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compra un plan para un usuario (crear membresía)"""
    
    # Solo personal autorizado puede crear membresías
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear membresías"
        )
    
    membership_service = MembershipService(db)
    membership = membership_service.create_membership_from_plan(
        user_id=user_id,
        plan_id=plan_id,
        payment_method=payment_method
    )
    
    return membership
