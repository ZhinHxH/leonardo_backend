from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.models.clinical_history import ClinicalHistory, UserGoal, RecordType
from app.services.clinical_history_service import ClinicalHistoryService
from app.core.logging_config import main_logger

logger = main_logger
router = APIRouter(tags=["clinical-history"])

# Schemas
class ClinicalRecordCreate(BaseModel):
    user_id: int
    record_type: RecordType
    weight: Optional[float] = None
    height: Optional[float] = None
    body_fat: Optional[float] = None
    muscle_mass: Optional[float] = None
    measurements: Optional[Dict[str, float]] = None
    notes: str = Field(..., min_length=1)
    recommendations: Optional[str] = None
    target_weight: Optional[float] = None
    target_body_fat: Optional[float] = None
    record_date: Optional[datetime] = None

class ClinicalRecordUpdate(BaseModel):
    record_type: Optional[RecordType] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    body_fat: Optional[float] = None
    muscle_mass: Optional[float] = None
    measurements: Optional[Dict[str, float]] = None
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    target_weight: Optional[float] = None
    target_body_fat: Optional[float] = None

class UserGoalCreate(BaseModel):
    user_id: int
    target_weight: Optional[float] = None
    target_body_fat: Optional[float] = None
    target_muscle_mass: Optional[float] = None
    target_date: Optional[datetime] = None
    description: str = Field(..., min_length=1)
    notes: Optional[str] = None

@router.get("/user/{user_id}")
async def get_user_clinical_history(
    user_id: int,
    record_type: Optional[str] = Query(None, description="Filtrar por tipo de registro"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la historia clínica de un usuario"""
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.TRAINER, UserRole.RECEPTIONIST] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver esta historia clínica"
        )
    
    clinical_service = ClinicalHistoryService(db)
    
    try:
        records = clinical_service.get_user_history(user_id, record_type)
        
        # Convertir a formato de respuesta
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "user_id": record.user_id,
                "date": record.record_date.isoformat(),
                "type": record.record_type,
                "weight": record.weight,
                "height": record.height,
                "body_fat": record.body_fat,
                "muscle_mass": record.muscle_mass,
                "measurements": record.measurements,
                "notes": record.notes,
                "recommendations": record.recommendations,
                "created_by": record.created_by.name if record.created_by else "Sistema",
                "created_at": record.created_at.isoformat()
            })
        
        return records_data
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo historia clínica: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_clinical_record(
    record_data: ClinicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo registro en la historia clínica"""
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.TRAINER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para crear registros clínicos"
        )
    
    clinical_service = ClinicalHistoryService(db)
    
    try:
        new_record = clinical_service.create_record(
            record_data=record_data.dict(),
            created_by_id=current_user.id
        )
        
        logger.info(f"✅ Registro clínico creado por {current_user.name}")
        
        return {
            "message": "Registro clínico creado exitosamente",
            "record": {
                "id": new_record.id,
                "user_id": new_record.user_id,
                "type": new_record.record_type,
                "date": new_record.record_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando registro clínico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{record_id}")
async def update_clinical_record(
    record_id: int,
    record_data: ClinicalRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza un registro de historia clínica"""
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.TRAINER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para actualizar registros clínicos"
        )
    
    clinical_service = ClinicalHistoryService(db)
    
    try:
        updated_record = clinical_service.update_record(
            record_id=record_id,
            record_data=record_data.dict(exclude_unset=True),
            updated_by_id=current_user.id
        )
        
        if not updated_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro no encontrado"
            )
        
        logger.info(f"✅ Registro clínico actualizado por {current_user.name}")
        
        return {
            "message": "Registro actualizado exitosamente",
            "record": {
                "id": updated_record.id,
                "type": updated_record.record_type,
                "date": updated_record.record_date.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando registro clínico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{record_id}")
async def delete_clinical_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un registro de historia clínica"""
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y gerentes pueden eliminar registros clínicos"
        )
    
    clinical_service = ClinicalHistoryService(db)
    
    try:
        success = clinical_service.delete_record(record_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro no encontrado"
            )
        
        logger.info(f"✅ Registro clínico eliminado por {current_user.name}")
        
        return {"message": "Registro eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando registro clínico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas del usuario"""
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.TRAINER, UserRole.RECEPTIONIST] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver estas estadísticas"
        )
    
    clinical_service = ClinicalHistoryService(db)
    
    try:
        stats = clinical_service.get_user_stats(user_id)
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/goals", status_code=status.HTTP_201_CREATED)
async def create_user_goal(
    goal_data: UserGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo objetivo para el usuario"""
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.TRAINER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para crear objetivos"
        )
    
    clinical_service = ClinicalHistoryService(db)
    
    try:
        new_goal = clinical_service.create_goal(
            goal_data=goal_data.dict(),
            created_by_id=current_user.id
        )
        
        logger.info(f"✅ Objetivo creado por {current_user.name}")
        
        return {
            "message": "Objetivo creado exitosamente",
            "goal": {
                "id": new_goal.id,
                "user_id": new_goal.user_id,
                "description": new_goal.description
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando objetivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


