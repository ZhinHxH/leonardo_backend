from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """Roles de usuario disponibles"""
    ADMIN = "admin"
    MANAGER = "manager"
    TRAINER = "trainer"
    RECEPTIONIST = "receptionist"
    MEMBER = "member"

class UserCreate(BaseModel):
    """Schema para creación de usuario"""
    email: EmailStr = Field(..., description="Correo electrónico único")
    password: str = Field(..., min_length=6, description="Contraseña")
    name: str = Field(..., min_length=2, max_length=100, description="Nombre completo")
    role: UserRole = Field(default=UserRole.MEMBER, description="Rol del usuario")
    phone: Optional[str] = Field(None, max_length=20, description="Número de teléfono")
    address: Optional[str] = Field(None, max_length=200, description="Dirección")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

class UserUpdate(BaseModel):
    """Schema para actualización de usuario"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nombre completo")
    role: Optional[UserRole] = Field(None, description="Rol del usuario")
    phone: Optional[str] = Field(None, max_length=20, description="Número de teléfono")
    address: Optional[str] = Field(None, max_length=200, description="Dirección")
    is_active: Optional[bool] = Field(None, description="Estado activo")

class UserInDB(BaseModel):
    """Schema para usuario en base de datos"""
    id: int = Field(..., description="ID del usuario")
    email: EmailStr = Field(..., description="Correo electrónico")
    name: str = Field(..., description="Nombre completo")
    role: UserRole = Field(..., description="Rol del usuario")
    phone: Optional[str] = Field(None, description="Número de teléfono")
    address: Optional[str] = Field(None, description="Dirección")
    is_active: bool = Field(..., description="Estado activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        from_attributes = True

class UserList(BaseModel):
    """Schema para lista de usuarios"""
    users: List[UserInDB] = Field(..., description="Lista de usuarios")
    total: int = Field(..., description="Total de usuarios")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Usuarios por página")

class UserProfile(BaseModel):
    """Schema para perfil de usuario"""
    id: int = Field(..., description="ID del usuario")
    email: EmailStr = Field(..., description="Correo electrónico")
    name: str = Field(..., description="Nombre completo")
    role: UserRole = Field(..., description="Rol del usuario")
    phone: Optional[str] = Field(None, description="Número de teléfono")
    address: Optional[str] = Field(None, description="Dirección")
    is_active: bool = Field(..., description="Estado activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    last_login: Optional[datetime] = Field(None, description="Último login")

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """Schema para respuesta de usuario"""
    id: int = Field(..., description="ID del usuario")
    email: EmailStr = Field(..., description="Correo electrónico")
    name: str = Field(..., description="Nombre completo")
    role: UserRole = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Estado activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        from_attributes = True



