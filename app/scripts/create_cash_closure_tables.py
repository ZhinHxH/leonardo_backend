#!/usr/bin/env python3
"""
Script para crear las tablas de cierre de caja en la base de datos
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import SessionLocal, engine
from app.models.cash_closure import CashClosure
from app.core.logging_config import main_logger

logger = main_logger

def create_cash_closure_tables():
    """Crea las tablas de cierre de caja"""
    print("Creando tablas de cierre de caja...")
    
    try:
        # Crear todas las tablas
        CashClosure.metadata.create_all(bind=engine)
        print("Tablas de cierre de caja creadas exitosamente")
        
        # Verificar que la tabla se creó
        db = SessionLocal()
        try:
            # Verificar que la tabla existe
            result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cash_closures'")
            table_exists = result.fetchone() is not None
            
            if table_exists:
                print("Tabla 'cash_closures' verificada")
            else:
                print("ERROR: Tabla 'cash_closures' no encontrada")
                return False
                
        except Exception as e:
            print(f"ERROR: Error verificando tabla: {e}")
            return False
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"ERROR: Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando creacion de tablas de cierre de caja...")
    
    success = create_cash_closure_tables()
    
    if success:
        print("\nTablas de cierre de caja creadas exitosamente!")
        print("Tablas creadas:")
        print("   - cash_closures")
        print("\nProximos pasos:")
        print("   1. Reinicia el servidor backend")
        print("   2. Verifica que las rutas de cierre de caja funcionen")
        print("   3. Prueba el componente de cierre de caja en el frontend")
    else:
        print("\nERROR: Error creando las tablas")
        sys.exit(1)

if __name__ == "__main__":
    main()
