from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.cash_closure import CashClosureStatus

class CashClosureBase(BaseModel):
    """Schema base para cierre de caja"""
    shift_date: datetime
    shift_start: datetime
    shift_end: Optional[datetime] = None
    notes: Optional[str] = None

class CashClosureCreate(CashClosureBase):
    """Schema para crear cierre de caja"""
    # Resumen de ventas
    total_sales: float = Field(0.0, ge=0)
    total_products_sold: int = Field(0, ge=0)
    total_memberships_sold: int = Field(0, ge=0)
    total_daily_access_sold: int = Field(0, ge=0)
    
    # Desglose por método de pago
    cash_sales: float = Field(0.0, ge=0)
    nequi_sales: float = Field(0.0, ge=0)
    bancolombia_sales: float = Field(0.0, ge=0)
    daviplata_sales: float = Field(0.0, ge=0)
    card_sales: float = Field(0.0, ge=0)
    transfer_sales: float = Field(0.0, ge=0)
    
    # Conteo físico
    cash_counted: float = Field(0.0, ge=0)
    nequi_counted: float = Field(0.0, ge=0)
    bancolombia_counted: float = Field(0.0, ge=0)
    daviplata_counted: float = Field(0.0, ge=0)
    card_counted: float = Field(0.0, ge=0)
    transfer_counted: float = Field(0.0, ge=0)
    
    # Notas sobre diferencias
    discrepancies_notes: Optional[str] = None

class CashClosureUpdate(BaseModel):
    """Schema para actualizar cierre de caja"""
    status: Optional[CashClosureStatus] = None
    notes: Optional[str] = None
    discrepancies_notes: Optional[str] = None
    reviewed_by_id: Optional[int] = None

class CashClosureResponse(CashClosureBase):
    """Schema de respuesta para cierre de caja"""
    id: int
    user_id: int
    total_sales: float
    total_products_sold: int
    total_memberships_sold: int
    total_daily_access_sold: int
    
    # Desglose por método de pago
    cash_sales: float
    nequi_sales: float
    bancolombia_sales: float
    daviplata_sales: float
    card_sales: float
    transfer_sales: float
    
    # Conteo físico
    cash_counted: float
    nequi_counted: float
    bancolombia_counted: float
    daviplata_counted: float
    card_counted: float
    transfer_counted: float
    
    # Diferencias
    cash_difference: float
    nequi_difference: float
    bancolombia_difference: float
    daviplata_difference: float
    card_difference: float
    transfer_difference: float
    
    # Estado y metadatos
    status: CashClosureStatus
    discrepancies_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    
    # Campos calculados
    total_counted: float
    total_differences: float
    has_discrepancies: bool
    
    class Config:
        from_attributes = True

class CashClosureListResponse(BaseModel):
    """Schema para lista de cierres de caja"""
    cash_closures: List[CashClosureResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class CashClosureSummary(BaseModel):
    """Schema para resumen de cierre de caja"""
    user_id: int
    user_name: str
    shift_date: datetime
    total_sales: float
    total_counted: float
    total_differences: float
    has_discrepancies: bool
    status: CashClosureStatus
    created_at: datetime

class CashClosureReport(BaseModel):
    """Schema para reporte de cierres de caja"""
    period_start: datetime
    period_end: datetime
    total_closures: int
    total_sales: float
    total_counted: float
    total_differences: float
    closures_with_discrepancies: int
    average_difference: float
    closures_by_user: List[dict]
    daily_summary: List[dict]
