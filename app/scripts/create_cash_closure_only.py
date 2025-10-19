#!/usr/bin/env python3
"""
Script para crear solo las tablas de cierre de caja
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine
from app.models.cash_closure import CashClosure
from app.core.logging_config import main_logger

logger = main_logger

def create_cash_closure_tables():
    """Crea solo las tablas de cierre de caja"""
    print("Creando tablas de cierre de caja...")
    
    try:
        # Crear solo la tabla de cierre de caja
        CashClosure.metadata.create_all(bind=engine)
        print("Tabla de cierre de caja creada exitosamente")
        return True
        
    except Exception as e:
        print(f"ERROR: Error creando tabla: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando creacion de tabla de cierre de caja...")
    
    success = create_cash_closure_tables()
    
    if success:
        print("\nTabla de cierre de caja creada exitosamente!")
        print("Tabla creada: cash_closures")
        print("\nProximos pasos:")
        print("   1. Reinicia el servidor backend")
        print("   2. Verifica que las rutas de cierre de caja funcionen")
    else:
        print("\nERROR: Error creando la tabla")
        sys.exit(1)

if __name__ == "__main__":
    main()
