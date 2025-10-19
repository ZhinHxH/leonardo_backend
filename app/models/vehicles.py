from sqlalchemy import Boolean, Column, Integer, String, Date, Enum, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class VehicleType(str, enum.Enum):
    """Tipos de vehículo disponibles"""
    CAR = "CAR"
    MOTORCYCLE = "MOTORCYCLE"
    BICYCLE = "BICYCLE"
    OTHER = "OTHER"

class Vehicle(Base):
    """Modelo para vehículos de los usuarios"""
    __tablename__ = "vehicles"

    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Información del vehículo
    plate = Column(String(20), nullable=False, index=True)  # Placa única
    vehicle_type = Column(Enum(VehicleType), default=VehicleType.CAR, nullable=False)
    brand = Column(String(100), nullable=True)  # Marca: Toyota, Honda, etc.
    model = Column(String(100), nullable=True)  # Modelo: Corolla, Civic, etc.
    color = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)  # Año del vehículo
    
    # Descripción adicional
    description = Column(Text, nullable=True)  # Descripción detallada
    
    # Estado y seguridad
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Si la información fue verificada
    
    # Campos de auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)  # Fecha de verificación
    
    # Relación con User - Asegúrate de que la ruta de importación sea correcta
    user = relationship("User", back_populates="vehicles")
    
    def __repr__(self):
        user_name = getattr(self.user, 'name', 'Unknown') if self.user else 'Unknown'
        return f"<Vehicle {self.plate} - {user_name}>"
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plate': self.plate,
            'vehicle_type': self.vehicle_type,
            'brand': self.brand,
            'model': self.model,
            'color': self.color,
            'year': self.year,
            'description': self.description,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'verified_at': self.verified_at
        }