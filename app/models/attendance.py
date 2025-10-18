from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class AccessMethod(str, enum.Enum):
    FACIAL = "facial"
    BARCODE = "barcode"
    MANUAL = "manual"

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    membership_id = Column(Integer, ForeignKey("memberships.id"))
    access_method = Column(Enum(AccessMethod))
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    notes = Column(String(500))
    
    # Relaciones
    user = relationship("User", back_populates="attendances")
    membership = relationship("Membership", back_populates="attendances")

    def __repr__(self):
        return f"<Attendance {self.id} - User {self.user_id}>" 