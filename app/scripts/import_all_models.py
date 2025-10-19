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
        
        # Importar modelo Vehicle desde su archivo separado
        from app.models.vehicle import Vehicle, VehicleType
        print("Modelos de vehículo importados")
        
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
        
        # Verificar que User tiene la relación con Vehicle
        if hasattr(User, 'vehicles'):
            print("Relacion vehicles encontrada en User")
        else:
            print("ERROR: Relacion vehicles NO encontrada en User")
            return False
            
        # Verificar que Vehicle tiene la relación con User
        if hasattr(Vehicle, 'user'):
            print("Relacion user encontrada en Vehicle")
        else:
            print("ERROR: Relacion user NO encontrada en Vehicle")
            return False
            
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
        from app.models.vehicle import Vehicle
        from app.models.cash_closure import CashClosure
        
        db = SessionLocal()
        
        # Intentar hacer una consulta simple para verificar que los modelos funcionan
        user_count = db.query(User).count()
        print(f"Usuarios en la base de datos: {user_count}")
        
        vehicle_count = db.query(Vehicle).count()
        print(f"Vehículos en la base de datos: {vehicle_count}")
        
        # Verificar que la relación funciona
        user = db.query(User).first()
        if user:
            print(f"Usuario encontrado: {user.email}")
            print(f"Relacion vehicles disponible: {hasattr(user, 'vehicles')}")
            print(f"Relacion cash_closures disponible: {hasattr(user, 'cash_closures')}")
        
        # Verificar que Vehicle funciona
        vehicle = db.query(Vehicle).first()
        if vehicle:
            print(f"Vehículo encontrado: {vehicle.plate}")
            print(f"Relacion user disponible: {hasattr(vehicle, 'user')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Error probando relaciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vehicle_model():
    """Prueba específica para el modelo Vehicle"""
    print("\nProbando modelo Vehicle...")
    
    try:
        from app.models.vehicle import Vehicle, VehicleType
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        
        # Crear una instancia de prueba del modelo Vehicle
        test_vehicle = Vehicle(
            user_id=1,  # Asumiendo que existe un usuario con ID 1
            plate="TEST123",
            vehicle_type=VehicleType.CAR,
            brand="Toyota",
            model="Corolla",
            color="Rojo",
            year=2020,
            description="Vehículo de prueba"
        )
        
        print(f"Vehículo de prueba creado: {test_vehicle}")
        print(f"Plate: {test_vehicle.plate}")
        print(f"Type: {test_vehicle.vehicle_type}")
        print(f"Brand: {test_vehicle.brand}")
        print(f"Model: {test_vehicle.model}")
        print(f"Color: {test_vehicle.color}")
        print(f"Year: {test_vehicle.year}")
        print(f"Description: {test_vehicle.description}")
        print(f"Is Active: {test_vehicle.is_active}")
        print(f"Is Verified: {test_vehicle.is_verified}")
        
        # Probar el método to_dict
        vehicle_dict = test_vehicle.to_dict()
        print(f"Dict del vehículo: {vehicle_dict}")
        
        db.close()
        print("✅ Modelo Vehicle probado exitosamente")
        return True
        
    except Exception as e:
        print(f"ERROR: Error probando modelo Vehicle: {e}")
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
    
    # Probar específicamente el modelo Vehicle
    if not test_vehicle_model():
        print("ERROR: Error probando modelo Vehicle")
        sys.exit(1)
    
    print("\nTodos los modelos importados y verificados correctamente!")
    print("El sistema deberia funcionar sin errores de dependencias circulares")

if __name__ == "__main__":
    main()