from sqlalchemy import Boolean, Column, Integer, String, Date, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    """Roles de usuario disponibles"""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    TRAINER = "TRAINER"
    RECEPTIONIST = "RECEPTIONIST"
    MEMBER = "MEMBER"

class BloodType(str, enum.Enum):
    """Tipos de sangre disponibles"""
    A_POSITIVE = "A_POSITIVE"
    A_NEGATIVE = "A_NEGATIVE"
    B_POSITIVE = "B_POSITIVE"
    B_NEGATIVE = "B_NEGATIVE"
    AB_POSITIVE = "AB_POSITIVE"
    AB_NEGATIVE = "AB_NEGATIVE"
    O_POSITIVE = "O_POSITIVE"
    O_NEGATIVE = "O_NEGATIVE"

class Gender(str, enum.Enum):
    """Géneros disponibles"""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class User(Base):
    """Modelo de usuario siguiendo principios SOLID"""
    __tablename__ = "users"

    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Cambiado de password a password_hash
    name = Column(String(255), nullable=False)  # Cambiado de full_name a name
    
    # Campos de identificación
    dni = Column(String(20), unique=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    blood_type = Column(Enum(BloodType), nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    
    # Campos de contacto
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    
    # Campos médicos
    eps = Column(String(100), nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    emergency_phone = Column(String(20), nullable=True)
    
    # Campos de seguridad y estado
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Campos biométricos
    facial_data = Column(Text, nullable=True)  # Almacena los datos biométricos faciales
    profile_picture = Column(String(255), nullable=True)  # URL de la foto de perfil
    
    # Campos de auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")
    fingerprints = relationship("Fingerprint", back_populates="user", cascade="all, delete-orphan")
    access_events = relationship("AccessEvent", back_populates="user", cascade="all, delete-orphan")
    clinical_records = relationship("ClinicalHistory", foreign_keys="ClinicalHistory.user_id", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("UserGoal", foreign_keys="UserGoal.user_id", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login
        } 