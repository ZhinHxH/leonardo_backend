from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class MembershipPlanBase(BaseModel):
    """Schema base para plan de membresía"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del plan")
    description: Optional[str] = Field(None, description="Descripción del plan")
    plan_type: str = Field(..., description="Tipo de plan: monthly, quarterly, yearly, daily")
    price: float = Field(..., gt=0, description="Precio del plan")
    discount_price: Optional[float] = Field(None, gt=0, description="Precio con descuento")
    duration_days: int = Field(..., gt=0, description="Duración en días")
    access_hours_start: Optional[str] = Field(None, description="Hora de inicio de acceso")
    access_hours_end: Optional[str] = Field(None, description="Hora de fin de acceso")
    includes_trainer: bool = Field(default=False, description="Incluye entrenador personal")
    includes_nutritionist: bool = Field(default=False, description="Incluye nutricionista")
    includes_pool: bool = Field(default=False, description="Incluye piscina")
    includes_classes: bool = Field(default=False, description="Incluye clases grupales")
    max_guests: int = Field(default=0, ge=0, description="Máximo de invitados")
    max_visits_per_day: Optional[int] = Field(None, gt=0, description="Máximo de visitas por día")
    max_visits_per_month: Optional[int] = Field(None, gt=0, description="Máximo de visitas por mes")
    is_active: bool = Field(default=True, description="Plan activo")
    is_popular: bool = Field(default=False, description="Plan popular")
    sort_order: int = Field(default=0, description="Orden de visualización")

class MembershipPlanCreate(MembershipPlanBase):
    """Schema para crear plan de membresía"""
    
    @validator('access_hours_start', 'access_hours_end')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError('El formato de hora debe ser HH:MM')
        return v

class MembershipPlanUpdate(BaseModel):
    """Schema para actualizar plan de membresía"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    plan_type: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    discount_price: Optional[float] = Field(None, gt=0)
    duration_days: Optional[int] = Field(None, gt=0)
    access_hours_start: Optional[str] = None
    access_hours_end: Optional[str] = None
    includes_trainer: Optional[bool] = None
    includes_nutritionist: Optional[bool] = None
    includes_pool: Optional[bool] = None
    includes_classes: Optional[bool] = None
    max_guests: Optional[int] = Field(None, ge=0)
    max_visits_per_day: Optional[int] = Field(None, gt=0)
    max_visits_per_month: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None
    sort_order: Optional[int] = None

class MembershipPlanResponse(MembershipPlanBase):
    """Schema para respuesta de plan de membresía"""
    id: int = Field(..., description="ID del plan")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        from_attributes = True

class RestockRequest(BaseModel):
    """Schema para solicitud de restock"""
    quantity: int = Field(..., gt=0, description="Cantidad a agregar")
    unit_cost: float = Field(..., gt=0, description="Costo unitario")
    new_selling_price: Optional[float] = Field(None, gt=0, description="Nuevo precio de venta (opcional)")
    supplier_name: str = Field(..., min_length=1, max_length=200, description="Nombre del proveedor")
    invoice_number: Optional[str] = Field(None, max_length=100, description="Número de factura")
    notes: Optional[str] = Field(None, description="Notas del restock")

class AccessValidationResponse(BaseModel):
    """Schema para respuesta de validación de acceso"""
    has_access: bool = Field(..., description="Si tiene acceso")
    reason: str = Field(..., description="Razón del acceso/denegación")
    membership: Optional[dict] = Field(None, description="Información de la membresía")
    plan: Optional[dict] = Field(None, description="Información del plan")

class PurchasePlanRequest(BaseModel):
    """Schema para compra de plan"""
    user_id: int = Field(..., description="ID del usuario")
    payment_method: str = Field(..., description="Método de pago")









