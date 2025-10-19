from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.services.sales_service import SalesService
from app.core.logging_config import main_logger

logger = main_logger
router = APIRouter(tags=["sales"])

# Schemas
class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: Optional[float] = None
    discount_percentage: float = Field(default=0.0, ge=0, le=100)

class MembershipItemCreate(BaseModel):
    plan_id: int
    customer_id: int
    payment_method: Optional[str] = "cash"

class CreateSaleRequest(BaseModel):
    customer_id: Optional[int] = None
    sale_type: str = Field(..., pattern="^(product|membership|mixed)$")
    payment_method: str = Field(..., pattern="^(cash|nequi|bancolombia|daviplata|card|transfer)$")
    amount_paid: float = Field(..., gt=0)
    discount_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None
    products: Optional[List[SaleItemCreate]] = []
    memberships: Optional[List[MembershipItemCreate]] = []

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": 1,
                "sale_type": "mixed",
                "payment_method": "cash",
                "amount_paid": 200000,
                "discount_amount": 0,
                "notes": "Venta de productos y membresía",
                "products": [
                    {
                        "product_id": 1,
                        "quantity": 1,
                        "unit_price": 89900,
                        "discount_percentage": 0
                    }
                ],
                "memberships": [
                    {
                        "plan_id": 1,
                        "customer_id": 1,
                        "payment_method": "cash"
                    }
                ]
            }
        }

class ReverseSaleRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Cliente solicitó devolución por producto defectuoso"
            }
        }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_data: CreateSaleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva venta completa con productos y/o membresías
    """
    
    # Verificar permisos
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para crear ventas"
        )
    
    # Validar que tenga al menos un item
    if not sale_data.products and not sale_data.memberships:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La venta debe incluir al menos un producto o membresía"
        )
    
    # Validar cliente para membresías
    if sale_data.memberships and not sale_data.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere cliente para ventas de membresías"
        )
    
    sales_service = SalesService(db)
    
    try:
        sale = sales_service.create_sale(
            sale_data=sale_data.dict(),
            seller_id=current_user.id
        )
        
        logger.info(f"✅ Venta creada por {current_user.name}: {sale.sale_number}")
        
        return {
            "message": "Venta creada exitosamente",
            "sale": sale,
            "sale_number": sale.sale_number
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando venta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/")
async def get_sales(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Estado de la venta"),
    seller_id: Optional[int] = Query(None, description="ID del vendedor"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(50, ge=1, le=100, description="Items por página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene lista de ventas con filtros y paginación
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver ventas"
        )
    
    # Convertir fechas si se proporcionan
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido para date_from (usar YYYY-MM-DD)"
            )
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido para date_to (usar YYYY-MM-DD)"
            )
    
    sales_service = SalesService(db)
    
    try:
        result = sales_service.get_sales(
            date_from=date_from_dt,
            date_to=date_to_dt,
            status=status,
            seller_id=seller_id,
            page=page,
            per_page=per_page
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo ventas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{sale_id}")
async def get_sale_details(
    sale_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles completos de una venta específica
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver detalles de ventas"
        )
    
    sales_service = SalesService(db)
    
    try:
        sale_details = sales_service.get_sale_details(sale_id)
        print(f"Sale Details: {sale_details}")
        return sale_details
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalles de venta {sale_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{sale_id}/reverse")
async def reverse_sale(
    sale_id: int,
    reverse_data: ReverseSaleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reversa una venta (solo administradores y gerentes)
    """
    
    # Verificar permisos estrictos para reversión
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y gerentes pueden reversar ventas"
        )
    
    sales_service = SalesService(db)
    
    try:
        success = sales_service.reverse_sale(
            sale_id=sale_id,
            reason=reverse_data.reason,
            reversed_by_id=current_user.id
        )
        
        if success:
            logger.info(f"✅ Venta {sale_id} reversada por {current_user.name}")
            return {
                "message": "Venta reversada exitosamente",
                "sale_id": sale_id,
                "reversed_by": current_user.name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo reversar la venta"
            )
            
    except Exception as e:
        logger.error(f"❌ Error reversando venta {sale_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/products/available")
async def get_products_for_sale(
    search: Optional[str] = Query(None, description="Término de búsqueda"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene productos disponibles para venta
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver productos"
        )
    
    sales_service = SalesService(db)
    
    try:
        products = sales_service.get_products_for_sale(search)
        return products
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo productos para venta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/membership-plans/available")
async def get_plans_for_sale(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene planes de membresía disponibles para venta
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver planes de membresía"
        )
    
    sales_service = SalesService(db)
    
    try:
        plans = sales_service.get_plans_for_sale()
        return plans
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo planes para venta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/summary/statistics")
async def get_sales_summary(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene resumen estadístico de ventas
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para ver estadísticas de ventas"
        )
    
    # Convertir fechas si se proporcionan
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido para date_from"
            )
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido para date_to"
            )
    
    sales_service = SalesService(db)
    
    try:
        summary = sales_service.get_sales_summary(
            date_from=date_from_dt,
            date_to=date_to_dt
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen de ventas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/validate-stock")
async def validate_stock(
    product_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Valida si hay stock suficiente para un producto
    """
    
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permisos para validar stock"
        )
    
    from app.models.inventory import Product
    
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return {"available": False, "reason": "Producto no encontrado"}
        
        if product.current_stock < quantity:
            return {
                "available": False,
                "reason": f"Stock insuficiente. Disponible: {product.current_stock}",
                "available_stock": product.current_stock
            }
        
        return {
            "available": True,
            "available_stock": product.current_stock
        }
        
    except Exception as e:
        logger.error(f"❌ Error validando stock: {e}")
        return {"available": False, "reason": "Error interno"}