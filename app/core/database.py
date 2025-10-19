from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de la base de datos
engine = create_engine(settings.DATABASE_URL)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la base para los modelos
Base = declarative_base()

# Función para importar modelos cuando sea necesario
def import_all_models():
    """Importa todos los modelos para resolver relaciones circulares"""
    try:
        # Importar modelos directamente sin usar __init__.py
        from app.models.user import User, UserRole, BloodType, Gender
        from app.models.membership import Membership, MembershipType, MembershipStatus, PaymentMethod
        # from app.models.clinical_history import ClinicalHistory, UserGoal, MembershipPlan, HistoryType
        from app.models.attendance import Attendance
        from app.models.inventory import Product, Category, ProductStatus, StockMovement, ProductCostHistory, InventoryReport, StockMovementType
        from app.models.sales import Sale, SaleType, SaleProductItem
        from app.models.fingerprint import Fingerprint, AccessEvent, DeviceConfig, FingerprintStatus, AccessEventStatus, DeviceType
        print("✅ Todos los modelos importados correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando modelos: {e}")
        return False

# NO importar modelos automáticamente para evitar imports circulares
# import_all_models()

# Función para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 