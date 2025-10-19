#!/usr/bin/env python3
"""
Script para migrar las tablas de ventas a la nueva estructura
"""

import sys
import os

# Agregar el directorio padre al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from sqlalchemy import create_engine, text, inspect
from core.config import settings
from core.database import Base, engine
from models.sales import (
    Sale, 
    SaleProductItem, 
    SaleMembershipItem, 
    SaleDailyAccessItem,
    SaleReversalLog
)

def check_table_exists(table_name):
    """Verifica si una tabla existe"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def drop_old_tables():
    """Elimina las tablas antiguas si existen"""
    print("🗑️ Eliminando tablas antiguas...")
    
    with engine.connect() as conn:
        # Eliminar tablas en orden inverso para evitar problemas de FK
        tables_to_drop = [
            'sale_reversal_logs',
            'sale_daily_access_items', 
            'sale_membership_items',
            'sale_product_items',
            'sale_items',  # Tabla antigua
            'membership_sales',  # Tabla antigua
            'sales'
        ]
        
        for table in tables_to_drop:
            if check_table_exists(table):
                print(f"   Eliminando tabla: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                conn.commit()

def create_new_tables():
    """Crea las nuevas tablas"""
    print("🏗️ Creando nuevas tablas...")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def verify_tables():
    """Verifica que las tablas se crearon correctamente"""
    print("🔍 Verificando tablas...")
    
    inspector = inspect(engine)
    expected_tables = [
        'sales',
        'sale_product_items',
        'sale_membership_items', 
        'sale_daily_access_items',
        'sale_reversal_logs'
    ]
    
    existing_tables = inspector.get_table_names()
    
    for table in expected_tables:
        if table in existing_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - FALTANTE")
            return False
    
    return True

def main():
    """Función principal"""
    print("🚀 Iniciando migración de tablas de ventas...")
    print("=" * 50)
    
    try:
        # 1. Eliminar tablas antiguas
        drop_old_tables()
        
        # 2. Crear nuevas tablas
        if not create_new_tables():
            return False
        
        # 3. Verificar que todo esté correcto
        if not verify_tables():
            print("❌ Error en la verificación de tablas")
            return False
        
        print("=" * 50)
        print("✅ Migración completada exitosamente!")
        print("📋 Tablas creadas:")
        print("   - sales (tabla principal)")
        print("   - sale_product_items (items de productos)")
        print("   - sale_membership_items (items de membresía)")
        print("   - sale_daily_access_items (acceso diario)")
        print("   - sale_reversal_logs (log de reversiones)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
