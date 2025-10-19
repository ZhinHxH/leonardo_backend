from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class CashClosureStatus(str, enum.Enum):
    """Estados del cierre de caja"""
    PENDING = "pending"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    CANCELLED = "cancelled"

class PaymentMethodType(str, enum.Enum):
    """Tipos de métodos de pago"""
    CASH = "cash"
    NEQUI = "nequi"
    BANCOLOMBIA = "bancolombia"
    DAVIPLATA = "daviplata"
    CARD = "card"
    TRANSFER = "transfer"

class CashClosure(Base):
    """Modelo para cierres de caja/turno"""
    __tablename__ = "cash_closures"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información del turno
    shift_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Resumen de ventas del turno
    total_sales = Column(Float, default=0.0, nullable=False)
    total_products_sold = Column(Integer, default=0, nullable=False)
    total_memberships_sold = Column(Integer, default=0, nullable=False)
    total_daily_access_sold = Column(Integer, default=0, nullable=False)
    
    # Desglose por método de pago
    cash_sales = Column(Float, default=0.0, nullable=False)
    nequi_sales = Column(Float, default=0.0, nullable=False)
    bancolombia_sales = Column(Float, default=0.0, nullable=False)
    daviplata_sales = Column(Float, default=0.0, nullable=False)
    card_sales = Column(Float, default=0.0, nullable=False)
    transfer_sales = Column(Float, default=0.0, nullable=False)
    
    # Conteo físico de efectivo
    cash_counted = Column(Float, default=0.0, nullable=False)  # Efectivo contado físicamente
    cash_difference = Column(Float, default=0.0, nullable=False)  # Diferencia entre sistema y físico
    
    # Otros métodos de pago contados
    nequi_counted = Column(Float, default=0.0, nullable=False)
    bancolombia_counted = Column(Float, default=0.0, nullable=False)
    daviplata_counted = Column(Float, default=0.0, nullable=False)
    card_counted = Column(Float, default=0.0, nullable=False)
    transfer_counted = Column(Float, default=0.0, nullable=False)
    
    # Diferencias por método de pago
    nequi_difference = Column(Float, default=0.0, nullable=False)
    bancolombia_difference = Column(Float, default=0.0, nullable=False)
    daviplata_difference = Column(Float, default=0.0, nullable=False)
    card_difference = Column(Float, default=0.0, nullable=False)
    transfer_difference = Column(Float, default=0.0, nullable=False)
    
    # Estado y observaciones
    status = Column(Enum(CashClosureStatus), default=CashClosureStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    discrepancies_notes = Column(Text, nullable=True)  # Notas sobre diferencias encontradas
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Quien revisó el cierre
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    user = relationship("User", foreign_keys=[user_id], back_populates="cash_closures")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    def __repr__(self):
        return f"<CashClosure {self.id} - {self.shift_date}>"
    
    @property
    def total_counted(self) -> float:
        """Total contado físicamente"""
        return (
            self.cash_counted + 
            self.nequi_counted + 
            self.bancolombia_counted + 
            self.daviplata_counted + 
            self.card_counted + 
            self.transfer_counted
        )
    
    @property
    def total_differences(self) -> float:
        """Total de diferencias encontradas"""
        return (
            self.cash_difference + 
            self.nequi_difference + 
            self.bancolombia_difference + 
            self.daviplata_difference + 
            self.card_difference + 
            self.transfer_difference
        )
    
    @property
    def has_discrepancies(self) -> bool:
        """Indica si hay diferencias significativas"""
        return abs(self.total_differences) > 0.01  # Tolerancia de 1 centavo
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'shift_date': self.shift_date,
            'shift_start': self.shift_start,
            'shift_end': self.shift_end,
            'total_sales': self.total_sales,
            'total_products_sold': self.total_products_sold,
            'total_memberships_sold': self.total_memberships_sold,
            'total_daily_access_sold': self.total_daily_access_sold,
            'cash_sales': self.cash_sales,
            'nequi_sales': self.nequi_sales,
            'bancolombia_sales': self.bancolombia_sales,
            'daviplata_sales': self.daviplata_sales,
            'card_sales': self.card_sales,
            'transfer_sales': self.transfer_sales,
            'cash_counted': self.cash_counted,
            'cash_difference': self.cash_difference,
            'nequi_counted': self.nequi_counted,
            'bancolombia_counted': self.bancolombia_counted,
            'daviplata_counted': self.daviplata_counted,
            'card_counted': self.card_counted,
            'transfer_counted': self.transfer_counted,
            'nequi_difference': self.nequi_difference,
            'bancolombia_difference': self.bancolombia_difference,
            'daviplata_difference': self.daviplata_difference,
            'card_difference': self.card_difference,
            'transfer_difference': self.transfer_difference,
            'status': self.status,
            'notes': self.notes,
            'discrepancies_notes': self.discrepancies_notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'reviewed_by_id': self.reviewed_by_id,
            'reviewed_at': self.reviewed_at,
            'total_counted': self.total_counted,
            'total_differences': self.total_differences,
            'has_discrepancies': self.has_discrepancies
        }
