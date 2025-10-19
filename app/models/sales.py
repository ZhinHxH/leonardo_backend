from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship, validates
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

class SalePaymentMethod(str, enum.Enum):
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
    
    #Disscount information
    is_discount = Column(Boolean, default=False, nullable=False)
    discount_reason= Column(String(100), default=None, nullable=True)
    discount_amount = Column(Float, default=0.0, nullable=False)

    @validates('discount_amount')
    def validate_discount_amount(self, key, discount_amount):
        """Valida que si is_discount es False, discount_amount sea 0"""
        # Si is_discount es None (aún no se ha establecido), permitir temporalmente
        if self.is_discount is None:
            return discount_amount
            
        if not self.is_discount and discount_amount > 0:
            raise ValueError(
                "No se puede tener un descuento mayor a 0 cuando is_discount es False. "
                f"is_discount: {self.is_discount}, discount_amount: {discount_amount}"
            )
        return discount_amount

    @validates('is_discount')
    def validate_is_discount(self, key, is_discount):
        """Si se desactiva el descuento, reinicia el monto y razón"""
        if not is_discount:
            # Reiniciar los valores de descuento cuando se desactiva
            self.discount_amount = 0.0
            self.discount_reason = "No reason available"
        return is_discount

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
    items = relationship("SaleProductItem", back_populates="sale", cascade="all, delete-orphan")
    membership_sales = relationship("SaleMembershipItem", back_populates="sale", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sale {self.sale_number} - {self.status}>"

    @property
    def can_be_reversed(self) -> bool:
        """Verifica si la venta puede ser reversada"""
        if self.is_reversed or self.status in ["cancelled", "refunded"]:
            return False
        
        # Si created_at es None, no se puede reversar
        if not self.created_at:
            return False
        
        # Solo se pueden reversar ventas del mismo día o hasta 24 horas después
        try:
            # Asegurarse de que created_at sea un datetime sin timezone para la comparación
            if hasattr(self.created_at, 'replace'):
                created_at_naive = self.created_at.replace(tzinfo=None)
            else:
                # Si no es un datetime, intentar convertirlo
                created_at_naive = self.created_at
                
            time_diff = datetime.utcnow() - created_at_naive
            return time_diff.days == 0  # Solo el mismo día
        except (AttributeError, TypeError):
            # En caso de cualquier error con el datetime, no permitir reversión
            return False



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

# Modelos adicionales para funcionalidad completa
class SaleDailyAccessItem(Base):
    """Modelo para ventas de acceso diario"""
    __tablename__ = "sale_daily_access_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información del acceso
    access_date = Column(DateTime(timezone=True), nullable=False)
    access_type = Column(String(50), default="daily", nullable=False)  # daily, hourly, etc.
    price = Column(Float, nullable=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    sale = relationship("Sale")
    user = relationship("User")

    def __repr__(self):
        return f"<SaleDailyAccessItem User:{self.user_id}>"

class SaleMembershipItem(Base):
    """Modelo para items de membresía en ventas"""
    __tablename__ = "sale_membership_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    membership_plan_id = Column(Integer, nullable=False)  # Sin FK por ahora
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información del plan
    plan_name = Column(String(100), nullable=False)
    plan_duration_days = Column(Integer, nullable=False)
    plan_price = Column(Float, nullable=False)
    
    # Fechas de la membresía
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    sale = relationship("Sale")
    user = relationship("User")
    # membership_plan = relationship("MembershipPlan", back_populates="sale_items")

    def __repr__(self):
        return f"<SaleMembershipItem {self.plan_name}>"

class SaleProductItem(Base):
    """Modelo para items de productos en ventas"""
    __tablename__ = "sale_product_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Información del producto al momento de la venta
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(50), nullable=True)
    
    # Cantidades y precios
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=True)
    discount_percentage = Column(Float, default=0.0)
    line_total = Column(Float, nullable=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    sale = relationship("Sale")
    product = relationship("Product")

    def __repr__(self):
        return f"<SaleProductItem {self.product_name} x{self.quantity}>"
