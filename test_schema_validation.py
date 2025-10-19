#!/usr/bin/env python3
"""
Script de prueba para validar el esquema de cierre de caja
"""

import sys
import os
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.schemas.cash_closure import CashClosureCreate

def test_schema_validation():
    """Prueba la validación del esquema con datos reales"""
    
    # Datos de prueba basados en el error 422
    test_data = {
        "shift_date": "2025-10-19",
        "shift_start": "2025-10-19T05:00:00.000Z",
        "shift_end": "2025-10-19T17:11:51.605Z",
        "notes": "",
        "total_sales": 169000,
        "total_products_sold": 2,
        "total_memberships_sold": 2,
        "total_daily_access_sold": 0,
        "cash_sales": 169000,
        "nequi_sales": 0,
        "bancolombia_sales": 0,
        "daviplata_sales": 0,
        "card_sales": 0,
        "transfer_sales": 0,
        "cash_counted": 168000,
        "nequi_counted": 0,
        "bancolombia_counted": 0,
        "daviplata_counted": 0,
        "card_counted": 0,
        "transfer_counted": 0,
        "discrepancies_notes": ""
    }
    
    try:
        print("🧪 Probando validación del esquema...")
        print(f"Datos de entrada: {test_data}")
        
        # Intentar crear el objeto
        cash_closure = CashClosureCreate(**test_data)
        
        print("✅ Validación exitosa!")
        print(f"Objeto creado: {cash_closure.dict()}")
        print(f"Tipos de fechas:")
        print(f"  shift_date: {type(cash_closure.shift_date)} = {cash_closure.shift_date}")
        print(f"  shift_start: {type(cash_closure.shift_start)} = {cash_closure.shift_start}")
        print(f"  shift_end: {type(cash_closure.shift_end)} = {cash_closure.shift_end}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de validación: {e}")
        print(f"Tipo de error: {type(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Iniciando prueba de validación del esquema...")
    test_schema_validation()
