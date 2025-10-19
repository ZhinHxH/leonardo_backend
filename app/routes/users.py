from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.core.logging_config import main_logger

from app.models.vehicles import VehicleType
from datetime import datetime

logger = main_logger
router = APIRouter(tags=["users"])

# Schema for vehicles
class VehicleBase(BaseModel):
    plate: str = Field(..., min_length=3, max_length=20, description="Placa del vehículo")
    vehicle_type: Optional[VehicleType] = VehicleType.CAR
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1)
    description: Optional[str] = None

class VehicleCreate(VehicleBase):
    user_id: int

class VehicleUpdate(BaseModel):
    plate: Optional[str] = Field(None, min_length=3, max_length=20)
    vehicle_type: Optional[VehicleType] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class VehicleResponse(VehicleBase):
    id: int
    user_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    verified_at: Optional[datetime]

    class Config:
        from_attributes = True

# Schemas
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: str
    password: str = Field(..., min_length=6)
    dni: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.MEMBER
    address: Optional[str] = Field(None, max_length=255)
    birth_date: Optional[str] = None
    blood_type: Optional[str] = None
    gender: Optional[str] = None
    eps: Optional[str] = Field(None, max_length=100)
    emergency_contact: Optional[str] = Field(None, max_length=255)
    emergency_phone: Optional[str] = Field(None, max_length=20)

    # Campos opcionales para vehículo
    has_vehicle: Optional[bool] = Field(False, description="Indica si el usuario tiene vehículo")
    vehicle_plate: Optional[str] = Field(None, min_length=3, max_length=20, description="Placa del vehículo")
    vehicle_type: Optional[VehicleType] = Field(None, description="Tipo de vehículo")
    vehicle_brand: Optional[str] = Field(None, max_length=100, description="Marca del vehículo")
    vehicle_model: Optional[str] = Field(None, max_length=100, description="Modelo del vehículo")
    vehicle_color: Optional[str] = Field(None, max_length=50, description="Color del vehículo")
    vehicle_year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1, description="Año del vehículo")
    vehicle_description: Optional[str] = Field(None, description="Descripción adicional del vehículo")

class VehicleInput(BaseModel):
    """Schema para crear/actualizar vehículos"""
    id: Optional[int] = None  # Si tiene ID, es actualización; si no, es creación
    plate: str = Field(..., min_length=3, max_length=20, description="Placa del vehículo")
    vehicle_type: VehicleType = VehicleType.CAR
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1)
    description: Optional[str] = None
    is_active: bool = True
    _action: Optional[str] = None  # 'delete' para marcar para eliminar

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    dni: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    address: Optional[str] = Field(None, max_length=255)
    birth_date: Optional[str] = None
    blood_type: Optional[str] = None
    gender: Optional[str] = None
    eps: Optional[str] = Field(None, max_length=100)
    emergency_contact: Optional[str] = Field(None, max_length=255)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    
    # Gestión de vehículos
    vehicles: Optional[list[VehicleInput]] = None

@router.get("/")
async def get_users(
    search: Optional[str] = Query(None, description="Término de búsqueda"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene lista de usuarios con filtros y paginación"""
    
    # Verificar permisos
    user_role_lower = current_user.role.lower() if current_user.role else 'member'
    if user_role_lower not in ['admin', 'manager', 'receptionist']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver usuarios"
        )
    
    user_service = UserService(db)
    
    try:
        result = user_service.get_users(
            search=search,
            skip=skip,
            limit=limit,
            role=role
        )
        
        # Convertir usuarios a formato de respuesta
        users_data = []
        for user in result['users']:
            # Obtener membresías activas del usuario
            active_memberships = []
            for membership in user.memberships:
                if membership.is_active:
                    active_memberships.append({
                        "id": membership.id,
                        "type": membership.type,
                        "start_date": membership.start_date.isoformat() if membership.start_date else "",
                        "end_date": membership.end_date.isoformat() if membership.end_date else "",
                        "price": membership.price,
                        "payment_method": membership.payment_method
                    })
            
            users_data.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "dni": user.dni,
                "phone": user.phone,
                "role": user.role.lower() if user.role else 'member',
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else "",
                "address": user.address,
                "memberships": active_memberships
            })
        
        return {
            "users": users_data,
            "total": result['total'],
            "page": (skip // limit) + 1,
            "per_page": limit,
            "total_pages": (result['total'] + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario"""
    
    # Verificar permisos
    user_role_lower = current_user.role.lower() if current_user.role else 'member'
    if user_role_lower not in ['admin', 'manager', 'receptionist']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para crear usuarios"
        )
    
    user_service = UserService(db)
    logger.info(f"Hasta acá va bien {user_data.dict()}")
    
    try:
        new_user = user_service.create_user(user_data.dict())
        
        logger.info(f"✅ Usuario creado por {current_user.name}: {new_user.email}")
        
        return {
            "message": "Usuario creado exitosamente",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"❌ Error creando usuario: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza un usuario existente"""
    
    # Verificar permisos
    user_role_lower = current_user.role.lower() if current_user.role else 'member'
    if user_role_lower not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para actualizar usuarios"
        )
    
    user_service = UserService(db)
    
    try:
        updated_user = user_service.update_user(user_id, user_data.dict(exclude_unset=True))
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        logger.info(f"✅ Usuario actualizado por {current_user.name}: {updated_user.email}")
        
        return {
            "message": "Usuario actualizado exitosamente",
            "user": {
                "id": updated_user.id,
                "name": updated_user.name,
                "email": updated_user.email,
                "role": updated_user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando usuario {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{user_id}/vehicles")
async def get_user_vehicles(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los vehículos de un usuario"""
    
    # Verificar permisos
    user_role_lower = current_user.role.lower() if current_user.role else 'member'
    if user_role_lower not in ['admin', 'manager', 'receptionist']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver vehículos"
        )
    
    try:
        from app.models.vehicles import Vehicle
        
        vehicles = db.query(Vehicle).filter(Vehicle.user_id == user_id).all()
        
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                "id": vehicle.id,
                "plate": vehicle.plate,
                "vehicle_type": vehicle.vehicle_type.value if hasattr(vehicle.vehicle_type, 'value') else vehicle.vehicle_type,
                "brand": vehicle.brand,
                "model": vehicle.model,
                "color": vehicle.color,
                "year": vehicle.year,
                "description": vehicle.description,
                "is_active": vehicle.is_active,
                "is_verified": vehicle.is_verified,
                "created_at": vehicle.created_at.isoformat() if vehicle.created_at else None
            })
        
        return {"vehicles": vehicles_data}
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo vehículos del usuario {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un usuario"""
    
    # Verificar permisos
    user_role_lower = current_user.role.lower() if current_user.role else 'member'
    if user_role_lower != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar usuarios"
        )
    
    user_service = UserService(db)
    
    try:
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        logger.info(f"✅ Usuario eliminado por {current_user.name}: ID {user_id}")
        
        return {"message": "Usuario eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando usuario {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/sellers")
async def get_sellers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene lista de vendedores disponibles para reportes
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver vendedores"
        )
    
    try:
        # Obtener usuarios que pueden ser vendedores
        sellers = db.query(User).filter(
            User.role.in_([UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]),
            User.is_active == True
        ).all()
        
        return [{"id": seller.id, "name": seller.name} for seller in sellers]
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo vendedores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
