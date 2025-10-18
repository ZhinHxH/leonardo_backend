# Modelos de productos movidos a inventory.py para mejor organización
# Este archivo se mantiene para compatibilidad con imports existentes

from app.models.inventory import Product, Category as ProductCategory, ProductStatus, StockMovement, ProductCostHistory, InventoryReport, StockMovementType

# Re-exportar para compatibilidad
__all__ = ['Product', 'ProductCategory', 'ProductStatus', 'StockMovement', 'ProductCostHistory', 'InventoryReport', 'StockMovementType'] 