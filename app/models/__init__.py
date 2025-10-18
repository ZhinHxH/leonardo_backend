"""
Importación de todos los modelos en el orden correcto para evitar problemas de relaciones circulares.
"""

# Importar modelos base primero
from .user import User, UserRole, BloodType, Gender
from .membership import Membership, MembershipType, MembershipStatus, PaymentMethod
# from .clinical_history import ClinicalHistory, UserGoal, MembershipPlan, HistoryType
from .attendance import Attendance
from .inventory import Product, Category, ProductStatus, StockMovement, ProductCostHistory, InventoryReport, StockMovementType
from .sales import Sale, SaleItem, MembershipSale, SaleReversalLog
from .fingerprint import Fingerprint, AccessEvent, DeviceConfig, FingerprintStatus, AccessEventStatus, DeviceType

# Exportar todos los modelos
__all__ = [
    # User models
    "User", "UserRole", "BloodType", "Gender",
    
    # Membership models
    "Membership", "MembershipType", "MembershipStatus", "PaymentMethod", "MembershipPlan",
    
    # Clinical History models (commented out - file doesn't exist)
    # "ClinicalHistory", "UserGoal", "HistoryType",
    
    # Attendance models
    "Attendance",
    
    # Inventory models
    "Product", "Category", "ProductStatus", "StockMovement", "ProductCostHistory", "InventoryReport", "StockMovementType",
    
    # Sale models
    "Sale", "SaleItem", "MembershipSale", "SaleReversalLog",
    
    # Fingerprint models
    "Fingerprint", "AccessEvent", "DeviceConfig", 
    "FingerprintStatus", "AccessEventStatus", "DeviceType"
]
