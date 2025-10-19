#!/usr/bin/env python3
"""
Script de prueba para el sistema de cierres de caja
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.sales import Sale
from app.models.user import User
from app.services.cash_closure_service import CashClosureService

def create_test_sales():
    """Crea ventas de prueba para el sistema"""
    db = SessionLocal()
    
    try:
        # Buscar un usuario para las pruebas
        user = db.query(User).first()
        if not user:
            print("❌ No se encontraron usuarios en la base de datos")
            return
        
        print(f"✅ Usuario encontrado: {user.name} (ID: {user.id})")
        
        # Crear ventas de prueba para hoy
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        test_sales = [
            {
                'sale_number': 'TEST-001',
                'customer_id': None,
                'seller_id': user.id,
                'sale_type': 'product',
                'status': 'completed',
                'subtotal': 10000,
                'tax_amount': 1900,
                'discount_amount': 0,
                'total_amount': 11900,
                'payment_method': 'cash',
                'amount_paid': 12000,
                'change_amount': 100,
                'created_at': today + timedelta(hours=9)
            },
            {
                'sale_number': 'TEST-002',
                'customer_id': None,
                'seller_id': user.id,
                'sale_type': 'membership',
                'status': 'completed',
                'subtotal': 50000,
                'tax_amount': 9500,
                'discount_amount': 0,
                'total_amount': 59500,
                'payment_method': 'nequi',
                'amount_paid': 59500,
                'change_amount': 0,
                'created_at': today + timedelta(hours=10)
            },
            {
                'sale_number': 'TEST-003',
                'customer_id': None,
                'seller_id': user.id,
                'sale_type': 'product',
                'status': 'completed',
                'subtotal': 25000,
                'tax_amount': 4750,
                'discount_amount': 0,
                'total_amount': 29750,
                'payment_method': 'card',
                'amount_paid': 29750,
                'change_amount': 0,
                'created_at': today + timedelta(hours=11)
            }
        ]
        
        # Crear las ventas
        for sale_data in test_sales:
            sale = Sale(**sale_data)
            db.add(sale)
        
        db.commit()
        print(f"✅ Creadas {len(test_sales)} ventas de prueba")
        
        # Probar el servicio de cierre de caja
        cash_closure_service = CashClosureService(db)
        shift_start = today
        
        print(f"\n🔍 Probando resumen de turno desde: {shift_start}")
        summary = cash_closure_service.get_shift_sales_summary(
            user_id=user.id,
            shift_start=shift_start
        )
        
        print("\n📊 Resumen del turno:")
        print(f"  Total ventas: ${summary['total_sales']:,.2f}")
        print(f"  Productos vendidos: {summary['total_products_sold']}")
        print(f"  Membresías vendidas: {summary['total_memberships_sold']}")
        print(f"  Ventas en efectivo: ${summary['cash_sales']:,.2f}")
        print(f"  Ventas en Nequi: ${summary['nequi_sales']:,.2f}")
        print(f"  Ventas con tarjeta: ${summary['card_sales']:,.2f}")
        print(f"  Total de ventas: {summary['sales_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def test_cash_closure_creation():
    """Prueba la creación de un cierre de caja"""
    db = SessionLocal()
    
    try:
        user = db.query(User).first()
        if not user:
            print("❌ No se encontraron usuarios")
            return False
        
        cash_closure_service = CashClosureService(db)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Obtener resumen
        summary = cash_closure_service.get_shift_sales_summary(
            user_id=user.id,
            shift_start=today
        )
        
        # Crear cierre de caja
        sales_data = {
            'total_sales': summary['total_sales'],
            'total_products_sold': summary['total_products_sold'],
            'total_memberships_sold': summary['total_memberships_sold'],
            'total_daily_access_sold': summary['total_daily_access_sold'],
            'cash_sales': summary['cash_sales'],
            'nequi_sales': summary['nequi_sales'],
            'bancolombia_sales': summary['bancolombia_sales'],
            'daviplata_sales': summary['daviplata_sales'],
            'card_sales': summary['card_sales'],
            'transfer_sales': summary['transfer_sales']
        }
        
        counted_data = {
            'cash_counted': summary['cash_sales'] + 100,  # Simular diferencia
            'nequi_counted': summary['nequi_sales'],
            'bancolombia_counted': summary['bancolombia_sales'],
            'daviplata_counted': summary['daviplata_sales'],
            'card_counted': summary['card_sales'],
            'transfer_counted': summary['transfer_sales']
        }
        
        cash_closure = cash_closure_service.create_cash_closure(
            user_id=user.id,
            shift_start=today,
            sales_data=sales_data,
            counted_data=counted_data,
            notes="Prueba de cierre de caja"
        )
        
        print(f"✅ Cierre de caja creado con ID: {cash_closure.id}")
        print(f"  Diferencias encontradas: ${cash_closure.total_differences:,.2f}")
        print(f"  Tiene discrepancias: {cash_closure.has_discrepancies}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando cierre de caja: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Iniciando pruebas del sistema de cierres de caja...")
    
    print("\n1️⃣ Creando ventas de prueba...")
    if create_test_sales():
        print("\n2️⃣ Probando creación de cierre de caja...")
        test_cash_closure_creation()
    
    print("\n✅ Pruebas completadas")
