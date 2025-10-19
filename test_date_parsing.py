#!/usr/bin/env python3
"""
Script para probar el parsing de fechas en el endpoint de reportes
"""

from datetime import datetime

def test_date_parsing():
    """Prueba el parsing de fechas como las que envía el frontend"""
    
    test_dates = [
        '2025-10-18',
        '2025-10-19', 
        '2025-01-01',
        '2024-12-31'
    ]
    
    print("🧪 Probando parsing de fechas...")
    print("=" * 50)
    
    for date_str in test_dates:
        try:
            parsed = datetime.fromisoformat(date_str)
            print(f'✅ {date_str} -> {parsed} (tipo: {type(parsed)})')
        except ValueError as e:
            print(f'❌ {date_str} -> Error: {e}')
    
    print("\n🔍 Probando con fechas del frontend...")
    print("=" * 50)
    
    # Simular las fechas que envía el frontend
    frontend_dates = [
        '2025-10-18',  # start_date
        '2025-10-18'   # end_date
    ]
    
    for i, date_str in enumerate(frontend_dates):
        try:
            parsed = datetime.fromisoformat(date_str)
            print(f'✅ Fecha {i+1}: {date_str} -> {parsed}')
        except ValueError as e:
            print(f'❌ Fecha {i+1}: {date_str} -> Error: {e}')

if __name__ == "__main__":
    test_date_parsing()
