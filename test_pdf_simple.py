#!/usr/bin/env python3
"""
Script simple para probar la generación de PDF
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_service import PDFService

def test_pdf_generation():
    """Prueba la generación de PDF con datos de ejemplo"""
    
    print("🧪 Probando generación de PDF...")
    
    # Datos de ejemplo
    closure_data = {
        'id': 1,
        'user_id': 1,
        'shift_date': '2025-01-19',
        'shift_start': '2025-01-19T05:00:00.000Z',
        'shift_end': '2025-01-19T17:00:00.000Z',
        'total_sales': 100000.0,
        'total_products_sold': 5,
        'total_memberships_sold': 2,
        'total_daily_access_sold': 0,
        'cash_sales': 50000.0,
        'nequi_sales': 30000.0,
        'bancolombia_sales': 20000.0,
        'daviplata_sales': 0.0,
        'card_sales': 0.0,
        'transfer_sales': 0.0,
        'cash_counted': 50000.0,
        'nequi_counted': 30000.0,
        'bancolombia_counted': 20000.0,
        'daviplata_counted': 0.0,
        'card_counted': 0.0,
        'transfer_counted': 0.0,
        'cash_difference': 0.0,
        'nequi_difference': 0.0,
        'bancolombia_difference': 0.0,
        'daviplata_difference': 0.0,
        'card_difference': 0.0,
        'transfer_difference': 0.0,
        'notes': 'Cierre de prueba',
        'status': 'PENDING'
    }
    
    items_data = {
        'items_sold': [
            {
                'product_id': 1,
                'product_name': 'Proteína Whey',
                'remaining_stock': 10,
                'unit_price': 50000.0,
                'quantity_sold': 2
            },
            {
                'product_id': 2,
                'product_name': 'Creatina',
                'remaining_stock': 5,
                'unit_price': 25000.0,
                'quantity_sold': 1
            }
        ],
        'total_items_sold': 3,
        'total_products_sold': 2
    }
    
    user_name = "Usuario de Prueba"
    
    try:
        # Crear instancia del servicio
        pdf_service = PDFService()
        print("✅ Servicio PDF creado correctamente")
        
        # Generar PDF
        print("📄 Generando PDF...")
        pdf_content = pdf_service.generate_cash_closure_pdf(closure_data, items_data, user_name)
        print(f"✅ PDF generado correctamente, tamaño: {len(pdf_content)} bytes")
        
        # Guardar PDF de prueba
        with open('test_closure.pdf', 'wb') as f:
            f.write(pdf_content)
        print("✅ PDF guardado como 'test_closure.pdf'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba de generación de PDF")
    print("=" * 50)
    
    success = test_pdf_generation()
    
    if success:
        print("\n✅ Prueba exitosa - El servicio PDF funciona correctamente")
    else:
        print("\n❌ Prueba fallida - Hay un problema en el servicio PDF")
