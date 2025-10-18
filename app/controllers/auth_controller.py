from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import main_logger, exception_handler, log_function_call
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    TokenResponse, 
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest
)
from app.schemas.user import UserResponse
from app.dependencies.auth import get_auth_service, get_current_user
from app.models.user import User

logger = main_logger

router = APIRouter()

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
@exception_handler(logger, {"endpoint": "/api/auth/login"})
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint para autenticación de usuarios
    
    Args:
        login_data: Datos de login (email y contraseña)
        db: Sesión de base de datos
        auth_service: Servicio de autenticación
    
    Returns:
        LoginResponse: Token de acceso e información del usuario
    
    Raises:
        HTTPException: Si las credenciales son incorrectas
    """
    logger.info(f"🌐 Endpoint /login llamado para email: {login_data.email}")
    
    try:
        logger.info("🔄 Delegando al servicio de autenticación...")
        result = auth_service.login_user(db, login_data)
        logger.info("✅ Login exitoso desde el controlador")
        return result
    except HTTPException as e:
        logger.warning(f"⚠️ HTTPException en login: {e.detail} (Status: {e.status_code})")
        raise
    except Exception as e:
        logger.error(f"💥 Error inesperado en endpoint login: {str(e)}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para cerrar sesión
    
    Args:
        current_user: Usuario actual autenticado
        db: Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    """
    # En una implementación más robusta, aquí se invalidaría el token
    return {"message": "Sesión cerrada exitosamente"}

@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint para refrescar token de acceso
    
    Args:
        refresh_data: Token de refresco
        db: Sesión de base de datos
        auth_service: Servicio de autenticación
    
    Returns:
        TokenResponse: Nuevo token de acceso
    
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        return auth_service.refresh_token(db, refresh_data.refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener información del usuario actual
    
    Args:
        current_user: Usuario actual autenticado
    
    Returns:
        UserResponse: Información del usuario
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.lower() if current_user.role else 'member',
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para solicitar reset de contraseña
    
    Args:
        reset_data: Email del usuario
        db: Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    """
    # TODO: Implementar lógica de envío de email
    return {"message": "Si el email existe, se enviará un enlace de reset"}

@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint para confirmar reset de contraseña
    
    Args:
        confirm_data: Token y nueva contraseña
        db: Sesión de base de datos
        auth_service: Servicio de autenticación
    
    Returns:
        dict: Mensaje de confirmación
    """
    # TODO: Implementar lógica de validación de token y cambio de contraseña
    return {"message": "Contraseña actualizada exitosamente"}

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint para cambiar contraseña del usuario actual
    
    Args:
        password_data: Contraseña actual y nueva
        current_user: Usuario actual autenticado
        db: Sesión de base de datos
        auth_service: Servicio de autenticación
    
    Returns:
        dict: Mensaje de confirmación
    
    Raises:
        HTTPException: Si la contraseña actual es incorrecta
    """
    try:
        # Verificar contraseña actual
        if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Generar nuevo hash
        new_password_hash = auth_service.get_password_hash(password_data.new_password)
        current_user.password_hash = new_password_hash
        
        db.commit()
        
        return {"message": "Contraseña actualizada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )



