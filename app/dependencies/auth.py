from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.user import UserRole

# Configurar el esquema de autenticación
security = HTTPBearer()

def get_auth_service() -> AuthService:
    """Dependencia para obtener el servicio de autenticación"""
    return AuthService()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependencia para obtener el usuario actual autenticado"""
    token = credentials.credentials
    user = auth_service.get_current_user(db, token)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependencia para obtener el usuario actual activo"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

def require_role(required_role: UserRole):
    """Dependencia para requerir un rol específico"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol {required_role}"
            )
        return current_user
    return role_checker

def require_any_role(required_roles: list[UserRole]):
    """Dependencia para requerir cualquiera de los roles especificados"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(required_roles)}"
            )
        return current_user
    return role_checker

# Dependencias predefinidas para roles comunes
require_admin = require_role(UserRole.ADMIN)
require_manager = require_role(UserRole.MANAGER)
require_trainer = require_role(UserRole.TRAINER)
require_receptionist = require_role(UserRole.RECEPTIONIST)
require_member = require_role(UserRole.MEMBER)

# Dependencias para roles administrativos
require_admin_or_manager = require_any_role([UserRole.ADMIN, UserRole.MANAGER])
require_staff = require_any_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.TRAINER, UserRole.RECEPTIONIST])





