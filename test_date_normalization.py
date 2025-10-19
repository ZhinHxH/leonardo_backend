#!/usr/bin/env python3
"""
Script de prueba para verificar la normalización de fechas en el servicio de inventario.
"""

from datetime import datetime, timedelta

def _normalize_date_range(date_from: str = None, date_to: str = None):
    """
    Normaliza el rango de fechas para que date_to sea el final del día especificado.
    """
    normalized_from = date_from
    normalized_to = date_to
    
    if date_to:
        # Convertir date_to al final del día (23:59:59.999999)
        try:
            date_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Agregar 23 horas, 59 minutos, 59 segundos y 999999 microsegundos
            end_of_day = date_obj + timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
            normalized_to = end_of_day.strftime('%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            print(f"Formato de fecha inválido para date_to: {date_to}")
            pass
    
    if date_from:
        # Asegurar que date_from sea el inicio del día (00:00:00)
        try:
            date_obj = datetime.strptime(date_from, '%Y-%m-%d')
            start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            normalized_from = start_of_day.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Formato de fecha inválido para date_from: {date_from}")
            pass
    
    return normalized_from, normalized_to

def test_date_normalization():
    """Prueba la normalización de fechas con diferentes casos"""
    
    test_cases = [
        {
            "name": "Caso 1: Solo fecha de inicio",
            "date_from": "2024-01-15",
            "date_to": None,
            "expected_from": "2024-01-15 00:00:00",
            "expected_to": None
        },
        {
            "name": "Caso 2: Solo fecha de fin",
            "date_from": None,
            "date_to": "2024-01-15",
            "expected_from": None,
            "expected_to": "2024-01-15 23:59:59.999999"
        },
        {
            "name": "Caso 3: Rango completo",
            "date_from": "2024-01-01",
            "date_to": "2024-01-31",
            "expected_from": "2024-01-01 00:00:00",
            "expected_to": "2024-01-31 23:59:59.999999"
        },
        {
            "name": "Caso 4: Mismo día",
            "date_from": "2024-01-15",
            "date_to": "2024-01-15",
            "expected_from": "2024-01-15 00:00:00",
            "expected_to": "2024-01-15 23:59:59.999999"
        }
    ]
    
    print("🧪 Probando normalización de fechas...")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Input: date_from='{case['date_from']}', date_to='{case['date_to']}'")
        
        result_from, result_to = _normalize_date_range(case['date_from'], case['date_to'])
        
        print(f"   Output: date_from='{result_from}', date_to='{result_to}'")
        
        # Verificar resultados
        from_ok = result_from == case['expected_from']
        to_ok = result_to == case['expected_to']
        
        if from_ok and to_ok:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            if not from_ok:
                print(f"   Expected from: '{case['expected_from']}'")
                print(f"   Got from: '{result_from}'")
            if not to_ok:
                print(f"   Expected to: '{case['expected_to']}'")
                print(f"   Got to: '{result_to}'")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    test_date_normalization()
