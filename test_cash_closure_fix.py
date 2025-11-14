#!/usr/bin/env python3
"""
Script de prueba para verificar que la corrección del sistema de cierre de caja funciona correctamente.
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.cash_closure_service import CashClosureService
from app.models.cash_closure import CashClosure

def test_cash_closure_logic():
    """Prueba la lógica de detección de cierres existentes"""
    
    print("=== Prueba de lógica de cierre de caja ===")
    
    # Obtener sesión de base de datos
    db = next(get_db())
    service = CashClosureService(db)
    
    # Datos de prueba
    user_id = 1
    shift_start = datetime(2025, 10, 20, 5, 0)  # 20 de octubre de 2025, 5:00 AM
    shift_date = shift_start.date()
    
    print(f"Usuario ID: {user_id}")
    print(f"Fecha del turno: {shift_date}")
    print(f"Fecha actual: {datetime.utcnow().date()}")
    
    # Verificar si existe un cierre para esta fecha
    existing_closure = db.query(CashClosure)\
                         .filter(CashClosure.user_id == user_id)\
                         .filter(CashClosure.shift_date == shift_date)\
                         .first()
    
    if existing_closure:
        print(f"✅ Encontrado cierre existente: ID {existing_closure.id}")
        print(f"   Fecha del cierre: {existing_closure.shift_date}")
        print(f"   Estado: {existing_closure.status}")
        print(f"   Total ventas: ${existing_closure.total_sales:,.2f}")
    else:
        print("❌ No se encontró cierre existente")
        
        # Buscar en rango de fechas cercanas
        start_date = shift_date - timedelta(days=1)
        end_date = shift_date + timedelta(days=1)
        
        nearby_closure = db.query(CashClosure)\
                           .filter(CashClosure.user_id == user_id)\
                           .filter(CashClosure.shift_date >= start_date)\
                           .filter(CashClosure.shift_date <= end_date)\
                           .first()
        
        if nearby_closure:
            print(f"🔍 Encontrado cierre cercano: ID {nearby_closure.id}")
            print(f"   Fecha del cierre: {nearby_closure.shift_date}")
            print(f"   Diferencia de días: {(nearby_closure.shift_date - shift_date).days}")
        else:
            print("🔍 No se encontraron cierres cercanos")
    
    # Listar todos los cierres del usuario
    all_closures = db.query(CashClosure)\
                     .filter(CashClosure.user_id == user_id)\
                     .order_by(CashClosure.shift_date.desc())\
                     .limit(5)\
                     .all()
    
    print(f"\n=== Últimos 5 cierres del usuario {user_id} ===")
    for closure in all_closures:
        print(f"ID: {closure.id}, Fecha: {closure.shift_date}, Estado: {closure.status}, Ventas: ${closure.total_sales:,.2f}")
    
    db.close()
    print("\n=== Prueba completada ===")

if __name__ == "__main__":
    test_cash_closure_logic()

