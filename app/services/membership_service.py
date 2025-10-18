from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from app.models.clinical_history import MembershipPlan
from app.models.membership import Membership, MembershipStatus
from app.models.user import User
from app.core.logging_config import main_logger, exception_handler

logger = main_logger

class MembershipService:
    """Servicio para gestión de planes de membresía"""
    
    def __init__(self, db: Session):
        self.db = db

    @exception_handler(logger, {"service": "MembershipService", "method": "get_plans"})
    def get_plans(self, include_inactive: bool = False) -> List[MembershipPlan]:
        """Obtiene lista de planes de membresía"""
        
        query = self.db.query(MembershipPlan)
        
        if not include_inactive:
            query = query.filter(MembershipPlan.is_active == True)
            
        return query.order_by(MembershipPlan.sort_order, MembershipPlan.name).all()

    @exception_handler(logger, {"service": "MembershipService", "method": "create_plan"})
    def create_plan(self, plan_data: Dict[str, Any]) -> MembershipPlan:
        """Crea un nuevo plan de membresía"""
        
        # Verificar unicidad del nombre
        existing = self.db.query(MembershipPlan).filter(MembershipPlan.name == plan_data['name']).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un plan con ese nombre"
            )
        
        plan = MembershipPlan(**plan_data)
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"✅ Plan creado: {plan.name} (ID: {plan.id})")
        return plan

    @exception_handler(logger, {"service": "MembershipService", "method": "update_plan"})
    def update_plan(self, plan_id: int, plan_data: Dict[str, Any]) -> MembershipPlan:
        """Actualiza un plan existente"""
        
        plan = self.db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        # Verificar unicidad del nombre si cambió
        if 'name' in plan_data and plan_data['name'] != plan.name:
            existing = self.db.query(MembershipPlan).filter(MembershipPlan.name == plan_data['name']).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un plan con ese nombre"
                )
        
        # Actualizar campos
        for field, value in plan_data.items():
            if hasattr(plan, field):
                setattr(plan, field, value)
        
        plan.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"✅ Plan actualizado: {plan.name} (ID: {plan.id})")
        return plan

    @exception_handler(logger, {"service": "MembershipService", "method": "delete_plan"})
    def delete_plan(self, plan_id: int) -> bool:
        """Elimina un plan (soft delete)"""
        
        plan = self.db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        # Verificar si hay membresías activas usando este plan
        # Nota: Como el modelo Membership no tiene plan_id, simplificamos esto
        # active_memberships = self.db.query(Membership).filter(
        #     Membership.plan_id == plan_id,
        #     Membership.is_active == True
        # ).count()
        
        # if active_memberships > 0:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"No se puede eliminar el plan. Tiene {active_memberships} membresías activas"
        #     )
        
        # Soft delete
        plan.is_active = False
        plan.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"✅ Plan eliminado: {plan.name} (ID: {plan.id})")
        return True

    @exception_handler(logger, {"service": "MembershipService", "method": "get_active_plans_for_sale"})
    def get_active_plans_for_sale(self) -> List[MembershipPlan]:
        """Obtiene planes activos disponibles para venta"""
        
        return self.db.query(MembershipPlan)\
                     .filter(MembershipPlan.is_active == True)\
                     .order_by(MembershipPlan.sort_order, MembershipPlan.price)\
                     .all()

    @exception_handler(logger, {"service": "MembershipService", "method": "validate_user_access"})
    def validate_user_access(self, user_id: int) -> Dict[str, Any]:
        """Valida si un usuario tiene acceso válido"""
        
        # Obtener membresía activa del usuario
        active_membership = self.db.query(Membership)\
                                  .filter(
                                      Membership.user_id == user_id,
                                      Membership.is_active == True,
                                      Membership.end_date > datetime.utcnow()
                                  ).first()
        
        if not active_membership:
            return {
                "has_access": False,
                "reason": "No tiene membresía activa",
                "current_plan": None,
                "membership_end_date": None
            }
        
        return {
            "has_access": True,
            "reason": "Membresía activa válida",
            "current_plan": active_membership.type.value if active_membership.type else None,
            "membership_end_date": active_membership.end_date,
            "payment_method": active_membership.payment_method.value if active_membership.payment_method else None
        }

    @exception_handler(logger, {"service": "MembershipService", "method": "get_plan_by_id"})
    def get_plan_by_id(self, plan_id: int) -> Optional[MembershipPlan]:
        """Obtiene un plan por ID"""
        
        plan = self.db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
        if not plan:
            return None
        
        return plan

    @exception_handler(logger, {"service": "MembershipService", "method": "create_membership_from_plan"})
    def create_membership_from_plan(self, user_id: int, plan_id: int, payment_method: str) -> Dict[str, Any]:
        """Crea una membresía basada en un plan"""
        
        # Obtener el plan
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        # Verificar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Desactivar membresías anteriores
        self.db.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.is_active == True
        ).update({"is_active": False})
        
        # Crear nueva membresía
        end_date = datetime.utcnow() + timedelta(days=plan.duration_days)
        
        # Mapear el nombre del plan a un tipo de membresía
        membership_type = "MONTHLY"  # Default
        if "quarterly" in plan.name.lower() or "trimestral" in plan.name.lower():
            membership_type = "QUARTERLY"
        elif "annual" in plan.name.lower() or "anual" in plan.name.lower():
            membership_type = "ANNUAL"
        elif "weekly" in plan.name.lower() or "semanal" in plan.name.lower():
            membership_type = "WEEKLY"
        
        new_membership = Membership(
            user_id=user_id,
            type=membership_type,
            start_date=datetime.utcnow(),
            end_date=end_date,
            price=plan.price,
            payment_method=payment_method,
            is_active=True
        )
        
        self.db.add(new_membership)
        self.db.commit()
        self.db.refresh(new_membership)
        
        logger.info(f"✅ Membresía creada: Usuario {user_id}, Plan {plan.name}")
        
        return {
            "membership_id": new_membership.id,
            "user_id": user_id,
            "plan_name": plan.name,
            "type": membership_type,
            "start_date": new_membership.start_date,
            "end_date": new_membership.end_date,
            "price": new_membership.price,
            "payment_method": new_membership.payment_method
        }
