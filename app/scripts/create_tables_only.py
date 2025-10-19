#!/usr/bin/env python3
"""
Script simple para crear solo las tablas de la base de datos
Sin datos de ejemplo - solo el esquema básico
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine, Base

# Importar todos los modelos para que SQLAlchemy los registre
from app.models.user import User, UserRole, BloodType, Gender
from app.models.membership import Membership, MembershipType, MembershipStatus, PaymentMethod
from app.models.clinical_history import ClinicalHistory, UserGoal, MembershipPlan, RecordType
from app.models.attendance import Attendance, AccessMethod
from app.models.inventory import (
    Product, Category, ProductStatus, StockMovement, 
    ProductCostHistory, InventoryReport, StockMovementType
)
from app.models.sales import Sale, SaleType, SaleProductItem
from app.models.fingerprint import (
    Fingerprint, AccessEvent, DeviceConfig, 
    FingerprintStatus, AccessEventStatus, DeviceType
)

def create_tables():
    """Crea todas las tablas de la base de datos"""
    print("🚀 Creando esquemas de base de datos...")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas creadas exitosamente:")
        print("  📋 users - Usuarios del sistema")
        print("  🏋️  memberships - Membresías de usuarios")
        print("  📊 clinical_history - Historial clínico")
        print("  🎯 user_goals - Objetivos de usuarios")
        print("  📋 membership_plans - Planes de membresía")
        print("  📅 attendances - Registro de asistencias")
        print("  📦 categories - Categorías de productos")
        print("  🛒 products - Inventario de productos")
        print("  📈 stock_movements - Movimientos de inventario")
        print("  💰 product_cost_history - Historial de costos")
        print("  📊 inventory_reports - Reportes de inventario")
        print("  💳 sales - Ventas realizadas")
        print("  🛍️  sale_items - Items de ventas")
        print("  👆 fingerprints - Huellas dactilares")
        print("  🚪 access_events - Eventos de acceso")
        print("  🔧 device_configs - Configuración de dispositivos")
        
        print("\n✅ ¡Esquemas de base de datos creados exitosamente!")
        print("💡 Para agregar datos de ejemplo, ejecute: install_database_schemas.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

if __name__ == "__main__":
    create_tables()
