from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    """Estados del producto"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class StockMovementType(str, Enum):
    """Tipos de movimiento de stock"""
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGE = "damage"
    EXPIRED = "expired"

# Schemas para Category
class CategoryBase(BaseModel):
    """Schema base para categoría"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la categoría")
    description: Optional[str] = Field(None, max_length=500, description="Descripción de la categoría")
    color: str = Field(default="#4CAF50", description="Color hex para la UI")
    icon: str = Field(default="category", description="Nombre del ícono")
    is_active: bool = Field(default=True, description="Estado activo de la categoría")
    sort_order: int = Field(default=0, description="Orden de visualización")

class CategoryCreate(CategoryBase):
    """Schema para crear categoría"""
    
    @validator('color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('El color debe ser un código hex válido (#RRGGBB)')
        return v

class CategoryUpdate(BaseModel):
    """Schema para actualizar categoría"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    
    @validator('color')
    def validate_color(cls, v):
        if v and (not v.startswith('#') or len(v) != 7):
            raise ValueError('El color debe ser un código hex válido (#RRGGBB)')
        return v

class CategoryResponse(CategoryBase):
    """Schema para respuesta de categoría"""
    id: int = Field(..., description="ID de la categoría")
    product_count: int = Field(default=0, description="Cantidad de productos en la categoría")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        from_attributes = True

# Schemas para Product
class ProductBase(BaseModel):
    """Schema base para producto"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del producto")
    description: Optional[str] = Field(None, description="Descripción del producto")
    category_id: Optional[int] = Field(None, description="ID de la categoría")
    barcode: Optional[str] = Field(None, max_length=100, description="Código de barras")
    sku: Optional[str] = Field(None, max_length=50, description="Stock Keeping Unit")
    current_cost: float = Field(..., ge=0, description="Costo actual de compra")
    selling_price: float = Field(..., gt=0, description="Precio de venta")
    current_stock: int = Field(default=0, ge=0, description="Stock actual")
    min_stock: int = Field(default=5, ge=0, description="Stock mínimo")
    max_stock: Optional[int] = Field(None, ge=0, description="Stock máximo")
    unit_of_measure: str = Field(default="unidad", description="Unidad de medida")
    weight_per_unit: Optional[float] = Field(None, ge=0, description="Peso por unidad")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Estado del producto")
    is_taxable: bool = Field(default=True, description="Si aplica impuestos")
    tax_rate: float = Field(default=19.0, ge=0, le=100, description="Tasa de impuesto")

class ProductCreate(ProductBase):
    """Schema para crear producto"""
    
    @validator('selling_price')
    def validate_selling_price(cls, v, values):
        if 'current_cost' in values and v <= values['current_cost']:
            raise ValueError('El precio de venta debe ser mayor al costo')
        return v

class ProductUpdate(BaseModel):
    """Schema para actualizar producto"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    current_cost: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, gt=0)
    current_stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    unit_of_measure: Optional[str] = None
    weight_per_unit: Optional[float] = Field(None, ge=0)
    status: Optional[ProductStatus] = None
    is_taxable: Optional[bool] = None
    tax_rate: Optional[float] = Field(None, ge=0, le=100)

class ProductResponse(ProductBase):
    """Schema para respuesta de producto"""
    id: int = Field(..., description="ID del producto")
    profit_margin: Optional[float] = Field(None, description="Margen de ganancia calculado")
    is_low_stock: bool = Field(default=False, description="Si tiene stock bajo")
    category_name: Optional[str] = Field(None, description="Nombre de la categoría")
    category_color: Optional[str] = Field(None, description="Color de la categoría")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    last_restock_date: Optional[datetime] = Field(None, description="Fecha del último restock")
    last_sale_date: Optional[datetime] = Field(None, description="Fecha de la última venta")

    class Config:
        from_attributes = True

# Schemas para StockMovement
class StockMovementBase(BaseModel):
    """Schema base para movimiento de stock"""
    product_id: int = Field(..., description="ID del producto")
    movement_type: StockMovementType = Field(..., description="Tipo de movimiento")
    quantity: int = Field(..., description="Cantidad (+ entrada, - salida)")
    unit_cost: Optional[float] = Field(None, ge=0, description="Costo unitario")
    total_cost: Optional[float] = Field(None, ge=0, description="Costo total")
    reference_number: Optional[str] = Field(None, max_length=100, description="Número de referencia")
    supplier: Optional[str] = Field(None, max_length=200, description="Proveedor")
    notes: Optional[str] = Field(None, description="Notas adicionales")

class StockMovementCreate(StockMovementBase):
    """Schema para crear movimiento de stock"""
    pass

class StockMovementResponse(StockMovementBase):
    """Schema para respuesta de movimiento de stock"""
    id: int = Field(..., description="ID del movimiento")
    user_id: int = Field(..., description="ID del usuario que hizo el movimiento")
    stock_before: int = Field(..., description="Stock antes del movimiento")
    stock_after: int = Field(..., description="Stock después del movimiento")
    movement_date: datetime = Field(..., description="Fecha del movimiento")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    
    # Información relacionada
    product_name: Optional[str] = Field(None, description="Nombre del producto")
    user_name: Optional[str] = Field(None, description="Nombre del usuario")

    class Config:
        from_attributes = True

# Schemas para ProductCostHistory
class ProductCostHistoryBase(BaseModel):
    """Schema base para historial de costos"""
    product_id: int = Field(..., description="ID del producto")
    cost_per_unit: float = Field(..., gt=0, description="Costo por unidad")
    quantity_purchased: int = Field(..., ge=0, description="Cantidad comprada")
    total_cost: float = Field(..., ge=0, description="Costo total")
    supplier_name: Optional[str] = Field(None, max_length=200, description="Nombre del proveedor")
    supplier_invoice: Optional[str] = Field(None, max_length=100, description="Número de factura")
    purchase_date: datetime = Field(..., description="Fecha de compra")
    notes: Optional[str] = Field(None, description="Notas adicionales")

class ProductCostHistoryCreate(ProductCostHistoryBase):
    """Schema para crear historial de costo"""
    pass

class ProductCostHistoryResponse(ProductCostHistoryBase):
    """Schema para respuesta de historial de costo"""
    id: int = Field(..., description="ID del registro")
    user_id: int = Field(..., description="ID del usuario que registró")
    currency: str = Field(default="COP", description="Moneda")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    
    # Información relacionada
    product_name: Optional[str] = Field(None, description="Nombre del producto")
    user_name: Optional[str] = Field(None, description="Nombre del usuario")

    class Config:
        from_attributes = True

# Schemas para operaciones especiales
class RestockRequest(BaseModel):
    """Schema para solicitud de restock"""
    quantity: int = Field(..., gt=0, description="Cantidad a agregar")
    unit_cost: float = Field(..., gt=0, description="Costo unitario")
    new_selling_price: Optional[float] = Field(None, gt=0, description="Nuevo precio de venta (opcional)")
    supplier_name: str = Field(..., min_length=1, max_length=200, description="Nombre del proveedor")
    invoice_number: Optional[str] = Field(None, max_length=100, description="Número de factura")
    notes: Optional[str] = Field(None, description="Notas del restock")

class InventorySummary(BaseModel):
    """Schema para resumen de inventario"""
    total_products: int = Field(..., description="Total de productos activos")
    total_categories: int = Field(..., description="Total de categorías activas")
    low_stock_count: int = Field(..., description="Productos con stock bajo")
    out_of_stock_count: int = Field(..., description="Productos sin stock")
    total_inventory_value: float = Field(..., description="Valor total del inventario")
    total_inventory_cost: Optional[float] = Field(None, description="Costo total del inventario")
    estimated_profit: Optional[float] = Field(None, description="Ganancia estimada")

class ProductListResponse(BaseModel):
    """Schema para lista de productos con paginación"""
    products: List[ProductResponse] = Field(..., description="Lista de productos")
    total: int = Field(..., description="Total de productos")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Productos por página")
    has_next: bool = Field(..., description="Si hay página siguiente")
    has_prev: bool = Field(..., description="Si hay página anterior")

class CategoryListResponse(BaseModel):
    """Schema para lista de categorías"""
    categories: List[CategoryResponse] = Field(..., description="Lista de categorías")
    total: int = Field(..., description="Total de categorías")

# Schemas para reportes
class SalesAnalysisResponse(BaseModel):
    """Schema para análisis de ventas"""
    product_id: int = Field(..., description="ID del producto")
    product_name: str = Field(..., description="Nombre del producto")
    category_name: str = Field(..., description="Nombre de la categoría")
    total_sold: int = Field(..., description="Total vendido")
    total_revenue: float = Field(..., description="Ingresos totales")
    total_profit: float = Field(..., description="Ganancia total")
    avg_selling_price: float = Field(..., description="Precio promedio de venta")
    last_sale_date: Optional[datetime] = Field(None, description="Fecha de última venta")

class InventoryAlert(BaseModel):
    """Schema para alertas de inventario"""
    product_id: int = Field(..., description="ID del producto")
    product_name: str = Field(..., description="Nombre del producto")
    current_stock: int = Field(..., description="Stock actual")
    min_stock: int = Field(..., description="Stock mínimo")
    alert_type: str = Field(..., description="Tipo de alerta")
    severity: str = Field(..., description="Severidad de la alerta")
    message: str = Field(..., description="Mensaje de la alerta")

class BulkUpdateRequest(BaseModel):
    """Schema para actualización masiva"""
    product_ids: List[int] = Field(..., description="IDs de productos a actualizar")
    update_data: ProductUpdate = Field(..., description="Datos a actualizar")

class BulkUpdateResponse(BaseModel):
    """Schema para respuesta de actualización masiva"""
    updated_count: int = Field(..., description="Cantidad de productos actualizados")
    failed_count: int = Field(..., description="Cantidad de productos que fallaron")
    errors: List[str] = Field(default=[], description="Lista de errores")

# Schemas para exportación
class ExportRequest(BaseModel):
    """Schema para solicitud de exportación"""
    format: str = Field(..., description="Formato de exportación (excel, csv, pdf)")
    include_costs: bool = Field(default=False, description="Incluir costos en la exportación")
    category_ids: Optional[List[int]] = Field(None, description="IDs de categorías a incluir")
    status_filter: Optional[str] = Field(None, description="Filtro por estado")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")

class ExportResponse(BaseModel):
    """Schema para respuesta de exportación"""
    file_url: str = Field(..., description="URL del archivo generado")
    file_name: str = Field(..., description="Nombre del archivo")
    file_size: int = Field(..., description="Tamaño del archivo en bytes")
    generated_at: datetime = Field(..., description="Fecha de generación")
    expires_at: datetime = Field(..., description="Fecha de expiración del enlace")
