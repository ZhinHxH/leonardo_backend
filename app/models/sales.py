from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class SaleStatus(str, enum.Enum):
    """Estados de la venta"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SaleType(str, enum.Enum):
    """Tipos de venta"""
    PRODUCT = "product"
    MEMBERSHIP = "membership"
    MIXED = "mixed"  # Productos + membresía

class PaymentMethod(str, enum.Enum):
    """Métodos de pago"""
    CASH = "cash"
    NEQUI = "nequi"
    BANCOLOMBIA = "bancolombia"
    DAVIPLATA = "daviplata"
    CARD = "card"
    TRANSFER = "transfer"

class Sale(Base):
    """Modelo mejorado para ventas"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    sale_number = Column(String(20), unique=True, nullable=False)  # Número de venta único
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Cliente (opcional para ventas rápidas)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Vendedor
    
    # Tipo y estado
    sale_type = Column(String(20), default="product", nullable=False)
    status = Column(String(20), default="completed", nullable=False)
    
    # Montos
    subtotal = Column(Float, default=0.0, nullable=False)  # Subtotal sin impuestos
    tax_amount = Column(Float, default=0.0, nullable=False)  # Monto de impuestos
    discount_amount = Column(Float, default=0.0, nullable=False)  # Descuentos aplicados
    total_amount = Column(Float, nullable=False)  # Total final
    
    # Pago
    payment_method = Column(String(20), nullable=False)
    amount_paid = Column(Float, nullable=False)  # Monto pagado
    change_amount = Column(Float, default=0.0, nullable=False)  # Cambio devuelto
    
    # Información adicional
    notes = Column(Text, nullable=True)
    receipt_printed = Column(Boolean, default=False)
    
    # Reversión
    is_reversed = Column(Boolean, default=False, nullable=False)
    reversed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reversed_at = Column(DateTime(timezone=True), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    
    # Fechas
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relaciones
    customer = relationship("User", foreign_keys=[customer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    reversed_by_user = relationship("User", foreign_keys=[reversed_by])
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    membership_sales = relationship("MembershipSale", back_populates="sale", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sale {self.sale_number} - {self.status}>"

    @property
    def can_be_reversed(self) -> bool:
        """Verifica si la venta puede ser reversada"""
        if self.is_reversed or self.status in ["cancelled", "refunded"]:
            return False
        
        # Solo se pueden reversar ventas del mismo día o hasta 24 horas después
        time_diff = datetime.utcnow() - self.created_at.replace(tzinfo=None)
        return time_diff.days == 0  # Solo el mismo día

class SaleItem(Base):
    """Modelo para items de venta (productos)"""
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Información del producto al momento de la venta
    product_name = Column(String(255), nullable=False)  # Nombre al momento de venta
    product_sku = Column(String(50), nullable=True)
    
    # Cantidades y precios
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Precio unitario al momento de venta
    unit_cost = Column(Float, nullable=True)  # Costo unitario (para cálculo de ganancia)
    discount_percentage = Column(Float, default=0.0)  # Descuento aplicado
    line_total = Column(Float, nullable=False)  # Total de la línea
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sales")

    def __repr__(self):
        return f"<SaleItem {self.product_name} x{self.quantity}>"

class MembershipSale(Base):
    """Modelo para ventas de membresías"""
    __tablename__ = "membership_sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    membership_plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False)
    membership_id = Column(Integer, ForeignKey("memberships.id"), nullable=True)  # Se crea después
    
    # Información del plan al momento de la venta
    plan_name = Column(String(100), nullable=False)
    plan_duration_days = Column(Integer, nullable=False)
    plan_price = Column(Float, nullable=False)
    
    # Fechas de la membresía
    membership_start_date = Column(DateTime(timezone=True), nullable=False)
    membership_end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    sale = relationship("Sale", back_populates="membership_sales")
    # membership_plan = relationship("MembershipPlan")
    membership = relationship("Membership")

    def __repr__(self):
        return f"<MembershipSale {self.plan_name}>"

class SaleReversalLog(Base):
    """Modelo para log de reversiones de ventas"""
    __tablename__ = "sale_reversal_logs"

    id = Column(Integer, primary_key=True, index=True)
    original_sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    reversed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información de la reversión
    reason = Column(Text, nullable=False)
    products_restocked = Column(Text, nullable=True)  # JSON con productos reabastecidos
    memberships_cancelled = Column(Text, nullable=True)  # JSON con membresías canceladas
    
    # Montos
    refunded_amount = Column(Float, nullable=False)
    
    # Metadatos
    reversed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    original_sale = relationship("Sale")
    reversed_by_user = relationship("User")

    def __repr__(self):
        return f"<SaleReversalLog Sale:{self.original_sale_id}>"
