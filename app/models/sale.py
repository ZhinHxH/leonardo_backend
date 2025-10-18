from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class SaleType(str, enum.Enum):
    MEMBERSHIP = "membership"
    PRODUCT = "product"
    DAILY_ACCESS = "daily_access"

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(SaleType))
    total_amount = Column(Float)
    payment_method = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(500))
    
    # Relaciones
    seller = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")

    def __repr__(self):
        return f"<Sale {self.id} - {self.type}>"

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    
    # Relaciones
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sales")

    def __repr__(self):
        return f"<SaleItem {self.id} - Sale {self.sale_id}>" 