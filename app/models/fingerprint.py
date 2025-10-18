from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class FingerprintStatus(str, enum.Enum):
    """Estado de la huella dactilar"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"

class AccessEventStatus(str, enum.Enum):
    """Estado del evento de acceso"""
    GRANTED = "granted"
    DENIED = "denied"
    ERROR = "error"

class DeviceType(str, enum.Enum):
    """Tipo de dispositivo de control de acceso"""
    ZKT_STANDALONE = "zk_standalone"
    INBIO_PANEL = "inbio_panel"
    OTHER = "other"


class Fingerprint(Base):
    """Modelo para almacenar huellas dactilares de usuarios"""
    __tablename__ = "fingerprints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Datos de la huella
    fingerprint_template = Column(Text, nullable=False)  # Template de la huella
    fingerprint_id = Column(String(50), unique=True, nullable=False)  # ID en el dispositivo ZKTeco
    
    # Metadatos
    finger_index = Column(Integer, default=0)  # Índice del dedo (0-9)
    quality_score = Column(Integer, default=0)  # Calidad de la huella (0-100)
    
    # Estado y fechas
    status = Column(String(20), default=FingerprintStatus.ACTIVE)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relación con usuario
    user = relationship("User", back_populates="fingerprints")
    
    # Relación con eventos de acceso
    access_events = relationship("AccessEvent", back_populates="fingerprint")


class AccessEvent(Base):
    """Modelo para registrar eventos de acceso"""
    __tablename__ = "access_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fingerprint_id = Column(Integer, ForeignKey("fingerprints.id"), nullable=True)
    
    # Información del evento
    event_type = Column(String(20), nullable=False)  # "access_granted", "access_denied", "enrollment"
    access_method = Column(String(20), default="fingerprint")  # "fingerprint", "manual", "card"
    
    # Resultado del acceso
    status = Column(String(20), default=AccessEventStatus.DENIED)  # Usar el enum
    denial_reason = Column(String(100), nullable=True)  # "expired_membership", "invalid_fingerprint", etc.
    
    # Información del dispositivo
    device_ip = Column(String(45), nullable=True)  # IP del dispositivo ZKTeco
    device_id = Column(String(50), nullable=True)  # ID del dispositivo
    
    # Timestamps
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="access_events")
    fingerprint = relationship("Fingerprint", back_populates="access_events")


class DeviceConfig(Base):
    """Configuración de dispositivos ZKTeco"""
    __tablename__ = "device_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String(100), nullable=False)
    device_ip = Column(String(45), nullable=False, unique=True)
    device_port = Column(Integer, default=4370)
    device_id = Column(String(50), unique=True, nullable=False)
    device_type = Column(String(20), default=DeviceType.INBIO_PANEL)  # Usar el enum
    
    # Configuración de acceso
    is_active = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=True)
    sync_interval = Column(Integer, default=300)  # segundos
    
    # Configuración de talanquera
    turnstile_enabled = Column(Boolean, default=True)
    turnstile_relay_port = Column(Integer, default=1)
    access_duration = Column(Integer, default=5)  # segundos que permanece abierta
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_connection = Column(DateTime(timezone=True), nullable=True)
