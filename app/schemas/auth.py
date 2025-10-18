from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Importar UserResponse al final para evitar import circular
from app.schemas.user import UserResponse

class LoginRequest(BaseModel):
    """Schema para solicitud de login"""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")

class TokenResponse(BaseModel):
    """Schema para respuesta de token"""
    access_token: str = Field(..., description="Token de acceso JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")

class LoginResponse(BaseModel):
    """Schema para respuesta de login"""
    access_token: str = Field(..., description="Token de acceso JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user: UserResponse = Field(..., description="Información del usuario")

class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de refresh token"""
    refresh_token: str = Field(..., description="Token de refresco")

class PasswordResetRequest(BaseModel):
    """Schema para solicitud de reset de contraseña"""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")

class PasswordResetConfirm(BaseModel):
    """Schema para confirmación de reset de contraseña"""
    token: str = Field(..., description="Token de reset")
    new_password: str = Field(..., min_length=6, description="Nueva contraseña")

class ChangePasswordRequest(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(..., min_length=6, description="Nueva contraseña")



