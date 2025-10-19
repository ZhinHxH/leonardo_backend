#!/usr/bin/env python3
"""
Script para importar todos los modelos y resolver dependencias circulares
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def import_all_models():
    """Importa todos los modelos en el orden correcto para resolver dependencias circulares"""
    print("Importando todos los modelos...")
    
    try:
        # Importar modelos base primero
        from app.models.user import User, UserRole, BloodType, Gender
        print("Modelos de usuario importados")
        
        from app.models.membership import Membership, MembershipType, MembershipStatus, PaymentMethod
        print("Modelos de membresia importados")
        
        from app.models.clinical_history import ClinicalHistory, UserGoal, MembershipPlan, HistoryType
        print("Modelos de historia clinica importados")
        
        from app.models.attendance import Attendance
        print("Modelos de asistencia importados")
        
        from app.models.inventory import Product, Category, ProductStatus, StockMovement, ProductCostHistory, InventoryReport, StockMovementType
        print("Modelos de inventario importados")
        
        from app.models.sales import Sale, SaleType, SaleStatus, SalePaymentMethod, SaleProductItem, SaleMembershipItem, SaleDailyAccessItem
        print("Modelos de ventas importados")
        
        from app.models.fingerprint import Fingerprint, AccessEvent, DeviceConfig, FingerprintStatus, AccessEventStatus, DeviceType
        print("Modelos de huellas dactilares importados")
        
        # Importar modelos de cierre de caja al final
        from app.models.cash_closure import CashClosure, CashClosureStatus, PaymentMethodType
        print("Modelos de cierre de caja importados")
        
        # Verificar que las relaciones se pueden resolver
        print("Verificando relaciones...")
        
        # Verificar que User tiene la relación con CashClosure
        if hasattr(User, 'cash_closures'):
            print("Relacion cash_closures encontrada en User")
        else:
            print("ERROR: Relacion cash_closures NO encontrada en User")
            return False
            
        # Verificar que CashClosure tiene la relación con User
        if hasattr(CashClosure, 'user'):
            print("Relacion user encontrada en CashClosure")
        else:
            print("ERROR: Relacion user NO encontrada en CashClosure")
            return False
            
        print("Todas las relaciones verificadas correctamente")
        return True
        
    except Exception as e:
        print(f"ERROR: Error importando modelos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_relationships():
    """Prueba que las relaciones entre modelos funcionen correctamente"""
    print("\nProbando relaciones entre modelos...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.models.cash_closure import CashClosure
        
        db = SessionLocal()
        
        # Intentar hacer una consulta simple para verificar que los modelos funcionan
        user_count = db.query(User).count()
        print(f"Usuarios en la base de datos: {user_count}")
        
        # Verificar que la relación funciona
        user = db.query(User).first()
        if user:
            print(f"Usuario encontrado: {user.email}")
            print(f"Relacion cash_closures disponible: {hasattr(user, 'cash_closures')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Error probando relaciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("Iniciando importacion de modelos...")
    
    # Importar todos los modelos
    if not import_all_models():
        print("ERROR: Error importando modelos")
        sys.exit(1)
    
    # Probar relaciones
    if not test_model_relationships():
        print("ERROR: Error probando relaciones")
        sys.exit(1)
    
    print("\nTodos los modelos importados y verificados correctamente!")
    print("El sistema deberia funcionar sin errores de dependencias circulares")

if __name__ == "__main__":
    main()
