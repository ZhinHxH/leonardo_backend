from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

from app.core.database import Base

class RecordType(str, Enum):
    """Tipos de registros clínicos"""
    INITIAL_ASSESSMENT = "initial_assessment"
    PROGRESS_CHECK = "progress_check"
    BODY_COMPOSITION = "body_composition"
    MEASUREMENTS = "measurements"
    MEDICAL_CLEARANCE = "medical_clearance"
    INJURY_REPORT = "injury_report"
    NUTRITION_PLAN = "nutrition_plan"
    TRAINING_PLAN = "training_plan"

class ClinicalHistory(Base):
    """Modelo para historia clínica de usuarios"""
    __tablename__ = "clinical_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50), nullable=False)
    record_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Medidas corporales
    weight = Column(Float, nullable=True)  # Peso en kg
    height = Column(Float, nullable=True)  # Altura en cm
    body_fat = Column(Float, nullable=True)  # Porcentaje de grasa corporal
    muscle_mass = Column(Float, nullable=True)  # Masa muscular en kg
    
    # Medidas adicionales (JSON para flexibilidad)
    measurements = Column(JSON, nullable=True)  # Medidas de circunferencias, etc.
    
    # Notas y observaciones
    notes = Column(Text, nullable=False)  # Notas principales del registro
    recommendations = Column(Text, nullable=True)  # Recomendaciones del entrenador/médico
    
    # Objetivos específicos del registro
    target_weight = Column(Float, nullable=True)
    target_body_fat = Column(Float, nullable=True)
    
    # Metadatos
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", foreign_keys=[user_id], back_populates="clinical_records")
    created_by = relationship("User", foreign_keys=[created_by_id])

class UserGoal(Base):
    """Modelo para objetivos de usuarios"""
    __tablename__ = "user_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Objetivos específicos
    target_weight = Column(Float, nullable=True)
    target_body_fat = Column(Float, nullable=True)
    target_muscle_mass = Column(Float, nullable=True)
    target_date = Column(DateTime, nullable=True)
    
    # Descripción y notas
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Estado del objetivo
    is_active = Column(Boolean, default=True)
    is_achieved = Column(Boolean, default=False)
    achieved_date = Column(DateTime, nullable=True)
    
    # Metadatos
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", foreign_keys=[user_id], back_populates="goals")
    created_by = relationship("User", foreign_keys=[created_by_id])

class MembershipPlan(Base):
    """Modelo para planes de membresía"""
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    plan_type = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    discount_price = Column(Float, nullable=True)
    duration_days = Column(Integer, nullable=False)
    
    # Horarios de acceso
    access_hours_start = Column(String(5), nullable=True)  # Formato HH:MM
    access_hours_end = Column(String(5), nullable=True)    # Formato HH:MM
    
    # Características incluidas
    includes_trainer = Column(Boolean, default=False)
    includes_nutritionist = Column(Boolean, default=False)
    includes_pool = Column(Boolean, default=False)
    includes_classes = Column(Boolean, default=False)
    
    # Límites
    max_guests = Column(Integer, default=0)
    max_visits_per_day = Column(Integer, nullable=True)
    max_visits_per_month = Column(Integer, nullable=True)
    
    # Estado y configuración
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MembershipPlan(name='{self.name}', price={self.price}, duration_days={self.duration_days})>"
