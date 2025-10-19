from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class ProductStatus(str, enum.Enum):
    """Estados del producto"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class StockMovementType(str, enum.Enum):
    """Tipos de movimiento de stock"""
    PURCHASE = "purchase"        # Compra/Restock
    SALE = "sale"               # Venta
    ADJUSTMENT = "adjustment"    # Ajuste de inventario
    RETURN = "return"           # Devolución
    DAMAGE = "damage"           # Producto dañado
    EXPIRED = "expired"         # Producto vencido

class Category(Base):
    """Modelo para categorías de productos"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Color hex para la UI
    icon = Column(String(50), nullable=True)  # Nombre del ícono
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relaciones
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"

class Product(Base):
    """Modelo mejorado para productos"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Información básica
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    sku = Column(String(50), unique=True, index=True, nullable=True)  # Stock Keeping Unit
    
    # Precios y costos
    current_cost = Column(Float, nullable=False, default=0.0)  # Costo actual de compra
    selling_price = Column(Float, nullable=False)  # Precio de venta
    profit_margin = Column(Float, nullable=True, default=0.0)  # Margen de ganancia
    
    # Stock
    current_stock = Column(Integer, default=0, nullable=False)
    min_stock = Column(Integer, default=5, nullable=False)  # Nivel mínimo para alertas
    max_stock = Column(Integer, nullable=True)  # Nivel máximo recomendado
    
    # Unidades y medidas
    unit_of_measure = Column(String(20), default="unidad", nullable=False)  # kg, lb, unidad, etc.
    weight_per_unit = Column(Float, nullable=True)  # Peso por unidad
    
    # Estado y configuración
    status = Column(String(20), default="active", nullable=False)
    is_taxable = Column(Boolean, default=True, nullable=False)
    tax_rate = Column(Float, default=19.0, nullable=False)  # IVA en Colombia
    
    # Fechas importantes
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_restock_date = Column(DateTime(timezone=True), nullable=True)
    last_sale_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    category = relationship("Category", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")
    cost_history = relationship("ProductCostHistory", back_populates="product", cascade="all, delete-orphan")
    sale_items = relationship("SaleProductItem", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name} - Stock: {self.current_stock}>"

    @property
    def is_low_stock(self) -> bool:
        """Verifica si el producto tiene stock bajo"""
        return self.current_stock <= self.min_stock

    @property
    def calculated_profit_margin(self) -> float:
        """Calcula el margen de ganancia: (precio - costo) / precio * 100"""
        if self.selling_price > 0:
            return ((self.selling_price - self.current_cost) / self.selling_price) * 100
        return 0.0
    
    def get_profit_margin_from_db(self) -> float:
        """Obtiene el margen calculado por la BD"""
        # Esto se usará para obtener el valor de la columna generada
        return getattr(self, '_profit_margin', self.calculated_profit_margin)

class StockMovement(Base):
    """Modelo para movimientos de stock"""
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Quien hizo el movimiento
    
    # Información del movimiento
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positivo para entrada, negativo para salida
    unit_cost = Column(Float, nullable=True)  # Costo unitario (para compras)
    total_cost = Column(Float, nullable=True)  # Costo total del movimiento
    
    # Stock antes y después
    stock_before = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    
    # Información adicional
    reference_number = Column(String(100), nullable=True)  # Número de factura, orden, etc.
    supplier = Column(String(200), nullable=True)  # Proveedor (para compras)
    notes = Column(Text, nullable=True)
    
    # Metadatos
    movement_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    product = relationship("Product", back_populates="stock_movements")
    user = relationship("User")

    def __repr__(self):
        return f"<StockMovement {self.movement_type} - {self.quantity} units>"

class ProductCostHistory(Base):
    """Modelo para historial de costos de productos"""
    __tablename__ = "product_cost_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Quien registró el costo
    
    # Información del costo
    cost_per_unit = Column(Float, nullable=False)
    quantity_purchased = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Información del proveedor
    supplier_name = Column(String(200), nullable=True)
    supplier_invoice = Column(String(100), nullable=True)
    
    # Fechas
    purchase_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Información adicional
    notes = Column(Text, nullable=True)
    currency = Column(String(3), default="COP", nullable=False)
    
    # Relaciones
    product = relationship("Product", back_populates="cost_history")
    user = relationship("User")

    def __repr__(self):
        return f"<CostHistory {self.product_id} - ${self.cost_per_unit}>"

class InventoryReport(Base):
    """Modelo para reportes de inventario generados"""
    __tablename__ = "inventory_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # 'sales_analysis', 'stock_alert', 'cost_analysis'
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Período del reporte
    date_from = Column(DateTime(timezone=True), nullable=False)
    date_to = Column(DateTime(timezone=True), nullable=False)
    
    # Datos del reporte (JSON)
    report_data = Column(Text, nullable=False)  # JSON con los datos del reporte
    
    # Metadatos
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    file_path = Column(String(500), nullable=True)  # Ruta del archivo exportado
    
    # Relaciones
    user = relationship("User")

    def __repr__(self):
        return f"<InventoryReport {self.report_type} - {self.generated_at}>"
