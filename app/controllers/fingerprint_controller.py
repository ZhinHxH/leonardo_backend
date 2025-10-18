from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.services.inbio_service import InBIOService
from app.models.fingerprint import Fingerprint, AccessEvent
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/fingerprint", tags=["fingerprint"])


# Schemas
class FingerprintEnrollRequest(BaseModel):
    user_id: int
    device_ip: str
    finger_index: int = 0


class FingerprintEnrollResponse(BaseModel):
    success: bool
    message: str
    fingerprint_id: Optional[int] = None


class AccessVerificationRequest(BaseModel):
    device_ip: str
    user_id: Optional[int] = None


class AccessVerificationResponse(BaseModel):
    access_granted: bool
    reason: Optional[str] = None
    message: str
    user: Optional[str] = None
    membership: Optional[str] = None


class FingerprintResponse(BaseModel):
    id: int
    user_id: int
    fingerprint_id: str
    finger_index: int
    quality_score: int
    status: str
    enrolled_at: datetime
    last_used: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccessEventResponse(BaseModel):
    id: int
    user_id: int
    event_type: str
    access_method: str
    access_granted: bool
    denial_reason: Optional[str] = None
    device_ip: Optional[str] = None
    event_time: datetime

    class Config:
        from_attributes = True


# Endpoints
@router.post("/enroll", response_model=FingerprintEnrollResponse)
async def enroll_fingerprint(
    request: FingerprintEnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enrola huella dactilar de un usuario
    """
    # Verificar permisos (solo admin, manager o receptionist pueden enrolar)
    if current_user.role not in ["admin", "manager", "receptionist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para enrolar huellas dactilares"
        )
    
    fingerprint_service = InBIOService(db)
    result = fingerprint_service.enroll_user_fingerprint(
        request.user_id, 
        request.device_ip, 
        request.finger_index
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return FingerprintEnrollResponse(**result)


@router.post("/verify-access", response_model=AccessVerificationResponse)
async def verify_access(
    request: AccessVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verifica acceso basado en huella dactilar y membresía
    """
    fingerprint_service = InBIOService(db)
    result = fingerprint_service.verify_access(
        request.device_ip, 
        request.user_id
    )
    
    return AccessVerificationResponse(**result)


@router.get("/user/{user_id}", response_model=List[FingerprintResponse])
async def get_user_fingerprints(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene huellas dactilares de un usuario
    """
    # Verificar permisos (solo puede ver sus propias huellas o ser admin/manager)
    if current_user.id != user_id and current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas huellas dactilares"
        )
    
    fingerprint_service = InBIOService(db)
    fingerprints = fingerprint_service.get_user_fingerprints(user_id)
    
    return [FingerprintResponse.from_orm(fp) for fp in fingerprints]


@router.delete("/{fingerprint_id}")
async def delete_fingerprint(
    fingerprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una huella dactilar
    """
    # Verificar permisos
    if current_user.role not in ["admin", "manager", "receptionist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar huellas dactilares"
        )
    
    fingerprint_service = InBIOService(db)
    success = fingerprint_service.delete_fingerprint(fingerprint_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Huella dactilar no encontrada"
        )
    
    return {"message": "Huella dactilar eliminada exitosamente"}


@router.get("/access-events", response_model=List[AccessEventResponse])
async def get_access_events(
    user_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene eventos de acceso
    """
    # Verificar permisos
    if current_user.role not in ["admin", "manager"]:
        # Los usuarios normales solo pueden ver sus propios eventos
        user_id = current_user.id
    
    fingerprint_service = InBIOService(db)
    events = fingerprint_service.get_access_events(user_id, limit)
    
    return [AccessEventResponse.from_orm(event) for event in events]


@router.get("/access-events/user/{user_id}", response_model=List[AccessEventResponse])
async def get_user_access_events(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene eventos de acceso de un usuario específico
    """
    # Verificar permisos
    if current_user.id != user_id and current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estos eventos de acceso"
        )
    
    fingerprint_service = InBIOService(db)
    events = fingerprint_service.get_access_events(user_id, limit)
    
    return [AccessEventResponse.from_orm(event) for event in events]


@router.get("/device/{device_ip}/status")
async def get_device_status(
    device_ip: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verifica el estado de conexión de un panel inBIO
    """
    # Verificar permisos
    if current_user.role not in ["admin", "manager", "receptionist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para verificar dispositivos"
        )
    
    fingerprint_service = InBIOService(db)
    result = fingerprint_service.get_device_status(device_ip)
    
    return {
        "device_ip": device_ip,
        "device_type": "inBIO",
        **result
    }


@router.post("/device/{device_ip}/sync-logs")
async def sync_device_logs(
    device_ip: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sincroniza logs de asistencia del panel inBIO
    """
    # Verificar permisos
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para sincronizar logs"
        )
    
    fingerprint_service = InBIOService(db)
    result = fingerprint_service.sync_attendance_logs(device_ip, limit)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result
