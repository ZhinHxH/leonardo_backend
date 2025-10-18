from sqlalchemy import Boolean, Column, Integer, String, Date, Enum, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime

class MembershipType(str, enum.Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    NEQUI = "nequi"
    BANCOLOMBIA = "bancolombia"
    DAVIPLATA = "daviplata"

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(MembershipType))  # Corregido para coincidir con la BD
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    price = Column(Float)
    payment_method = Column(Enum(PaymentMethod))
    is_active = Column(Boolean, default=True)  # Corregido para coincidir con la BD
    
    # Relaciones
    user = relationship("User", back_populates="memberships")
    attendances = relationship("Attendance", back_populates="membership")

    def __repr__(self):
        return f"<Membership {self.type} - User {self.user_id}>"

# MembershipPlan movido a clinical_history.py para evitar duplicación 