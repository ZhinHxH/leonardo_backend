from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.logging_config import main_logger, exception_handler
from app.services.inventory_service import InventoryService
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.inventory import Product, Category, ProductCostHistory
from app.schemas.inventory import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse,
    RestockRequest, InventorySummary, InventoryAlert,
    ProductCostHistoryResponse, StockMovementResponse,
    ExportRequest, ExportResponse
)

logger = main_logger
router = APIRouter(prefix="/inventory", tags=["inventory"])

# Los schemas ahora están importados desde app.schemas.inventory

@router.get("/products")
@exception_handler(logger, {"endpoint": "/inventory/products"})
async def get_products(
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_costs: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene lista de productos con filtros"""
    
    # Solo administradores pueden ver costos - validación robusta
    if include_costs and current_user.role.upper() != "ADMIN":
        include_costs = False
    
    inventory_service = InventoryService(db)
    result = inventory_service.get_products(
        category_id=category_id,
        status=status,
        search=search,
        include_costs=include_costs,
        page=page,
        per_page=per_page
    )
    
    return result

@router.post("/products", response_model=ProductResponse)
@exception_handler(logger, {"endpoint": "/inventory/products", "method": "POST"})
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuevo producto (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear productos"
        )
    
    inventory_service = InventoryService(db)
    product = inventory_service.create_product(
        product_data.dict(),
        current_user.id
    )
    
    return product

@router.put("/products/{product_id}")
@exception_handler(logger, {"endpoint": "/inventory/products/{product_id}", "method": "PUT"})
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza un producto (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden editar productos"
        )
    
    inventory_service = InventoryService(db)
    product = inventory_service.update_product(
        product_id,
        product_data.dict(exclude_unset=True),
        current_user.id
    )
    
    return product

@router.delete("/products/{product_id}")
@exception_handler(logger, {"endpoint": "/inventory/products/{product_id}", "method": "DELETE"})
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un producto (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar productos"
        )
    
    inventory_service = InventoryService(db)
    success = inventory_service.delete_product(product_id)
    
    return {"success": success, "message": "Producto eliminado exitosamente"}

@router.post("/products/{product_id}/restock", response_model=ProductResponse)
@exception_handler(logger, {"endpoint": "/inventory/products/{product_id}/restock"})
async def restock_product(
    product_id: int,
    restock_data: RestockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra restock de un producto (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden hacer restock"
        )
    
    inventory_service = InventoryService(db)
    product = inventory_service.restock_product(
        product_id=product_id,
        quantity=restock_data.quantity,
        unit_cost=restock_data.unit_cost,
        supplier_name=restock_data.supplier_name,
        user_id=current_user.id,
        new_selling_price=restock_data.new_selling_price,
        invoice_number=restock_data.invoice_number,
        notes=restock_data.notes
    )
    
    return product

@router.get("/products/{product_id}/cost-history")
@exception_handler(logger, {"endpoint": "/inventory/products/{product_id}/cost-history"})
async def get_product_cost_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene historial de costos de un producto (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver el historial de costos"
        )
    
    inventory_service = InventoryService(db)
    history = inventory_service.get_product_cost_history(product_id)
    
    return history

@router.get("/categories", response_model=List[CategoryResponse])
@exception_handler(logger, {"endpoint": "/inventory/categories"})
async def get_categories(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene lista de categorías"""
    
    inventory_service = InventoryService(db)
    categories = inventory_service.get_categories(include_inactive)
    
    return categories

@router.post("/categories", response_model=CategoryResponse)
@exception_handler(logger, {"endpoint": "/inventory/categories", "method": "POST"})
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva categoría (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear categorías"
        )
    
    inventory_service = InventoryService(db)
    category = inventory_service.create_category(category_data.dict())
    
    return category

@router.put("/categories/{category_id}", response_model=CategoryResponse)
@exception_handler(logger, {"endpoint": "/inventory/categories/{category_id}", "method": "PUT"})
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza una categoría (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden editar categorías"
        )
    
    inventory_service = InventoryService(db)
    category = inventory_service.update_category(
        category_id,
        category_data.dict(exclude_unset=True)
    )
    
    return category

@router.delete("/categories/{category_id}")
@exception_handler(logger, {"endpoint": "/inventory/categories/{category_id}", "method": "DELETE"})
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina una categoría (solo administradores)"""
    
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar categorías"
        )
    
    inventory_service = InventoryService(db)
    success = inventory_service.delete_category(category_id)
    
    return {"success": success, "message": "Categoría eliminada exitosamente"}

@router.get("/summary", response_model=InventorySummary)
@exception_handler(logger, {"endpoint": "/inventory/summary"})
async def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene resumen del inventario"""
    
    inventory_service = InventoryService(db)
    summary = inventory_service.get_inventory_summary()
    
    # Solo administradores ven costos
    if current_user.role.upper() != "ADMIN":
        summary.pop("total_inventory_cost", None)
        summary.pop("estimated_profit", None)
    
    return summary

@router.get("/alerts")
@exception_handler(logger, {"endpoint": "/inventory/alerts"})
async def get_inventory_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene alertas de inventario"""
    
    inventory_service = InventoryService(db)
    low_stock_products = inventory_service.get_low_stock_products()
    
    return {
        "low_stock_products": low_stock_products,
        "alert_count": len(low_stock_products)
    }

# Nuevos endpoints para reportes
@router.get("/reports/complete")
@exception_handler(logger, {"endpoint": "/inventory/reports/complete"})
async def get_complete_inventory_report(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene reporte completo de inventario"""
    
    inventory_service = InventoryService(db)
    report_data = inventory_service.get_complete_inventory_report(date_from, date_to)
    
    return report_data

@router.get("/reports/stock-movements")
@exception_handler(logger, {"endpoint": "/inventory/reports/stock-movements"})
async def get_stock_movements_report(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene movimientos de stock para reportes"""
    
    inventory_service = InventoryService(db)
    movements = inventory_service.get_stock_movements_report(date_from, date_to)
    
    return movements

@router.get("/reports/category-values")
@exception_handler(logger, {"endpoint": "/inventory/reports/category-values"})
async def get_category_values_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene valores por categoría para reportes"""
    
    inventory_service = InventoryService(db)
    category_values = inventory_service.get_category_values_report()
    
    return category_values

@router.get("/reports/top-products")
@exception_handler(logger, {"endpoint": "/inventory/reports/top-products"})
async def get_top_products_report(
    limit: int = Query(10, ge=1, le=50, description="Número de productos a retornar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene productos más vendidos para reportes"""
    
    inventory_service = InventoryService(db)
    top_products = inventory_service.get_top_products_report(limit)
    
    return top_products

@router.get("/reports/trends")
@exception_handler(logger, {"endpoint": "/inventory/reports/trends"})
async def get_inventory_trends_report(
    months: int = Query(6, ge=1, le=12, description="Número de meses a analizar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene tendencias del inventario para reportes"""
    
    inventory_service = InventoryService(db)
    trends = inventory_service.get_inventory_trends_report(months)
    
    return trends
