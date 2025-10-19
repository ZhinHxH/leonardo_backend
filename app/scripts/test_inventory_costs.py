#!/usr/bin/env python3
"""
Script para probar que los costos se muestren correctamente en el inventario
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import SessionLocal
from app.services.inventory_service import InventoryService
from app.models.user import User, UserRole

def test_inventory_costs():
    """Prueba que los costos se muestren correctamente para usuarios ADMIN"""
    print("🧪 Probando visualización de costos en inventario...")
    
    db = SessionLocal()
    inventory_service = InventoryService(db)
    
    try:
        # Simular usuario ADMIN
        admin_user = User()
        admin_user.role = UserRole.ADMIN
        
        print("👤 Usuario ADMIN - Debe mostrar costos:")
        result_admin = inventory_service.get_products(
            include_costs=True,
            page=1,
            per_page=5
        )
        
        if result_admin['products']:
            product = result_admin['products'][0]
            print(f"  📦 Producto: {product['name']}")
            print(f"  💰 Costo: {product['current_cost']}")
            print(f"  📊 Margen: {product['profit_margin']}")
            
            if product['current_cost'] is not None and product['current_cost'] > 0:
                print("  ✅ Costos mostrados correctamente")
            else:
                print("  ❌ Problema: Costos no se muestran")
        else:
            print("  ⚠️ No hay productos en la base de datos")
        
        print("\n👤 Usuario NO-ADMIN - No debe mostrar costos:")
        result_non_admin = inventory_service.get_products(
            include_costs=False,
            page=1,
            per_page=5
        )
        
        if result_non_admin['products']:
            product = result_non_admin['products'][0]
            print(f"  📦 Producto: {product['name']}")
            print(f"  💰 Costo: {product['current_cost']}")
            print(f"  📊 Margen: {product['profit_margin']}")
            
            if product['current_cost'] == 0:
                print("  ✅ Costos ocultos correctamente (valor 0)")
            else:
                print("  ❌ Problema: Costos visibles cuando no deberían")
        else:
            print("  ⚠️ No hay productos en la base de datos")
            
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
    finally:
        db.close()

def test_role_validation():
    """Prueba la validación de roles"""
    print("\n🔐 Probando validación de roles...")
    
    # Simular diferentes roles
    test_roles = [
        ("admin", "ADMIN", True),
        ("ADMIN", "ADMIN", True),
        ("Admin", "ADMIN", True),
        ("manager", "ADMIN", False),
        ("user", "ADMIN", False),
    ]
    
    for role, expected, should_match in test_roles:
        result = role.upper() == expected
        status = "✅" if result == should_match else "❌"
        print(f"  {status} Rol '{role}' -> {result} (esperado: {should_match})")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de inventario...")
    test_role_validation()
    test_inventory_costs()
    print("\n✅ Pruebas completadas")
