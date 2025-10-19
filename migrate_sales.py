#!/usr/bin/env python3
"""
Script simple para migrar las tablas de ventas
"""

import sys
import os

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.core.database import Base, engine
from app.models.sales import (
    Sale, 
    SaleProductItem, 
    SaleMembershipItem, 
    SaleDailyAccessItem,
    SaleReversalLog
)

def main():
    print("Iniciando migracion de tablas de ventas...")
    
    try:
        # Eliminar tablas antiguas si existen
        print("Eliminando tablas antiguas...")
        with engine.connect() as conn:
            tables_to_drop = [
                'sale_reversal_logs',
                'sale_daily_access_items', 
                'sale_membership_items',
                'sale_product_items',
                'sale_items',
                'membership_sales',
                'sales'
            ]
            
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    print(f"   Eliminada: {table}")
                except Exception as e:
                    print(f"   No se pudo eliminar {table}: {e}")
            
            conn.commit()
        
        # Crear nuevas tablas
        print("Creando nuevas tablas...")
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas exitosamente")
        
        # Verificar tablas
        print("Verificando tablas...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = [
            'sales',
            'sale_product_items',
            'sale_membership_items', 
            'sale_daily_access_items',
            'sale_reversal_logs'
        ]
        
        for table in expected_tables:
            if table in existing_tables:
                print(f"   OK: {table}")
            else:
                print(f"   ERROR: {table} - FALTANTE")
        
        print("=" * 50)
        print("Migracion completada!")
        return True
        
    except Exception as e:
        print(f"Error durante la migracion: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
