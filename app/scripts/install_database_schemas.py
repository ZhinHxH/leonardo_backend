#!/usr/bin/env python3
"""
Script completo para instalar todos los esquemas de la base de datos del gimnasio
Incluye creación de tablas, datos por defecto y configuración inicial
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine, SessionLocal, Base
from app.core.config import settings

# Importar todos los modelos para que SQLAlchemy los registre
from app.models.user import User, UserRole, BloodType, Gender
from app.models.membership import Membership, MembershipType, MembershipStatus, PaymentMethod
from app.models.clinical_history import ClinicalHistory, UserGoal, MembershipPlan, RecordType
from app.models.attendance import Attendance, AccessMethod
from app.models.inventory import (
    Product, Category, ProductStatus, StockMovement, 
    ProductCostHistory, InventoryReport, StockMovementType
)
from app.models.sales import Sale, SaleType, SaleProductItem
from app.models.fingerprint import (
    Fingerprint, AccessEvent, DeviceConfig, 
    FingerprintStatus, AccessEventStatus, DeviceType
)
from app.services.auth_service import AuthService

def print_header(title: str):
    """Imprime un encabezado formateado"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_success(message: str):
    """Imprime un mensaje de éxito"""
    print(f"✅ {message}")

def print_info(message: str):
    """Imprime un mensaje informativo"""
    print(f"ℹ️  {message}")

def print_error(message: str):
    """Imprime un mensaje de error"""
    print(f"❌ {message}")

def create_all_tables():
    """Crea todas las tablas de la base de datos"""
    print_header("CREANDO ESQUEMAS DE BASE DE DATOS")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print_success("Tablas principales creadas:")
        print("  📋 users - Usuarios del sistema")
        print("  🏋️  memberships - Membresías de usuarios")
        print("  📊 clinical_history - Historial clínico")
        print("  🎯 user_goals - Objetivos de usuarios")
        print("  📋 membership_plans - Planes de membresía")
        print("  📅 attendances - Registro de asistencias")
        print("  📦 categories - Categorías de productos")
        print("  🛒 products - Inventario de productos")
        print("  📈 stock_movements - Movimientos de inventario")
        print("  💰 product_cost_history - Historial de costos")
        print("  📊 inventory_reports - Reportes de inventario")
        print("  💳 sales - Ventas realizadas")
        print("  🛍️  sale_items - Items de ventas")
        print("  👆 fingerprints - Huellas dactilares")
        print("  🚪 access_events - Eventos de acceso")
        print("  🔧 device_configs - Configuración de dispositivos")
        
        return True
        
    except Exception as e:
        print_error(f"Error creando tablas: {e}")
        return False

def create_default_users():
    """Crea usuarios por defecto del sistema"""
    print_header("CREANDO USUARIOS POR DEFECTO")
    
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # Usuarios por defecto
        default_users = [
            {
                "email": "admin@gym.com",
                "password": "admin123",
                "name": "Administrador del Sistema",
                "role": UserRole.ADMIN,
                "dni": "12345678",
                "phone": "3001234567"
            },
            {
                "email": "manager@gym.com",
                "password": "manager123",
                "name": "Gerente del Gimnasio",
                "role": UserRole.MANAGER,
                "dni": "87654321",
                "phone": "3007654321"
            },
            {
                "email": "trainer@gym.com",
                "password": "trainer123",
                "name": "Entrenador Principal",
                "role": UserRole.TRAINER,
                "dni": "11223344",
                "phone": "3009876543"
            },
            {
                "email": "receptionist@gym.com",
                "password": "reception123",
                "name": "Recepcionista",
                "role": UserRole.RECEPTIONIST,
                "dni": "44332211",
                "phone": "3005555555"
            },
            {
                "email": "member@gym.com",
                "password": "member123",
                "name": "Miembro de Ejemplo",
                "role": UserRole.MEMBER,
                "dni": "99887766",
                "phone": "3001111111",
                "gender": Gender.MALE,
                "blood_type": BloodType.O_POSITIVE
            }
        ]
        
        created_count = 0
        for user_data in default_users:
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                continue
            
            # Crear hash de la contraseña
            password_hash = auth_service.get_password_hash(user_data["password"])
            
            # Crear usuario
            user = User(
                email=user_data["email"],
                password_hash=password_hash,
                name=user_data["name"],
                role=user_data["role"],
                dni=user_data.get("dni"),
                phone=user_data.get("phone"),
                gender=user_data.get("gender"),
                blood_type=user_data.get("blood_type"),
                is_active=True
            )
            
            db.add(user)
            created_count += 1
        
        db.commit()
        
        if created_count > 0:
            print_success(f"{created_count} usuarios creados exitosamente")
        else:
            print_info("Los usuarios por defecto ya existen")
            
        return True
        
    except Exception as e:
        print_error(f"Error creando usuarios: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_membership_plans():
    """Crea planes de membresía por defecto"""
    print_header("CREANDO PLANES DE MEMBRESÍA")
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen planes
        existing_plans = db.query(MembershipPlan).count()
        
        if existing_plans == 0:
            plans = [
                MembershipPlan(
                    name="Plan Básico Mensual",
                    description="Acceso completo al gimnasio durante un mes. Incluye uso de equipos y piscina.",
                    plan_type="monthly",
                    price=120000,
                    duration_days=30,
                    access_hours_start="06:00",
                    access_hours_end="22:00",
                    includes_trainer=False,
                    includes_nutritionist=False,
                    includes_pool=True,
                    includes_classes=True,
                    max_guests=0,
                    is_active=True,
                    is_popular=True,
                    sort_order=1
                ),
                MembershipPlan(
                    name="Plan Premium Mensual",
                    description="Acceso completo con entrenador personal y nutricionista incluidos.",
                    plan_type="monthly",
                    price=200000,
                    discount_price=180000,
                    duration_days=30,
                    access_hours_start="05:00",
                    access_hours_end="23:00",
                    includes_trainer=True,
                    includes_nutritionist=True,
                    includes_pool=True,
                    includes_classes=True,
                    max_guests=2,
                    is_active=True,
                    is_popular=False,
                    sort_order=2
                ),
                MembershipPlan(
                    name="Acceso Diario",
                    description="Acceso por un día al gimnasio. Ideal para visitantes ocasionales.",
                    plan_type="daily",
                    price=15000,
                    duration_days=1,
                    access_hours_start="06:00",
                    access_hours_end="22:00",
                    includes_trainer=False,
                    includes_nutritionist=False,
                    includes_pool=False,
                    includes_classes=False,
                    max_guests=0,
                    is_active=True,
                    is_popular=False,
                    sort_order=3
                ),
                MembershipPlan(
                    name="Plan Estudiante",
                    description="Plan especial para estudiantes con descuento y horarios flexibles.",
                    plan_type="monthly",
                    price=100000,
                    discount_price=80000,
                    duration_days=30,
                    access_hours_start="14:00",
                    access_hours_end="20:00",
                    includes_trainer=False,
                    includes_nutritionist=False,
                    includes_pool=True,
                    includes_classes=True,
                    max_guests=1,
                    is_active=True,
                    is_popular=False,
                    sort_order=4
                ),
                MembershipPlan(
                    name="Plan Trimestral",
                    description="Membresía por 3 meses con descuento especial.",
                    plan_type="quarterly",
                    price=320000,
                    discount_price=300000,
                    duration_days=90,
                    access_hours_start="06:00",
                    access_hours_end="22:00",
                    includes_trainer=False,
                    includes_nutritionist=False,
                    includes_pool=True,
                    includes_classes=True,
                    max_guests=1,
                    is_active=True,
                    is_popular=True,
                    sort_order=5
                )
            ]
            
            for plan in plans:
                db.add(plan)
            
            db.commit()
            print_success(f"{len(plans)} planes de membresía creados")
        else:
            print_info(f"Ya existen {existing_plans} planes de membresía")
            
        return True
        
    except Exception as e:
        print_error(f"Error creando planes de membresía: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_product_categories():
    """Crea categorías de productos por defecto"""
    print_header("CREANDO CATEGORÍAS DE PRODUCTOS")
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen categorías
        existing_categories = db.query(Category).count()
        
        if existing_categories == 0:
            categories = [
                Category(
                    name="Suplementos",
                    description="Proteínas, vitaminas y suplementos nutricionales",
                    color="#FF6B6B",
                    icon="supplement",
                    sort_order=1
                ),
                Category(
                    name="Bebidas",
                    description="Bebidas energéticas, agua y jugos naturales",
                    color="#4ECDC4",
                    icon="drink",
                    sort_order=2
                ),
                Category(
                    name="Snacks Saludables",
                    description="Barras energéticas, frutos secos y snacks nutritivos",
                    color="#45B7D1",
                    icon="snack",
                    sort_order=3
                ),
                Category(
                    name="Accesorios",
                    description="Guantes, correas, toallas y accesorios de entrenamiento",
                    color="#96CEB4",
                    icon="accessory",
                    sort_order=4
                ),
                Category(
                    name="Ropa Deportiva",
                    description="Camisetas, shorts y ropa deportiva del gimnasio",
                    color="#FFEAA7",
                    icon="clothing",
                    sort_order=5
                )
            ]
            
            for category in categories:
                db.add(category)
            
            db.commit()
            print_success(f"{len(categories)} categorías de productos creadas")
        else:
            print_info(f"Ya existen {existing_categories} categorías de productos")
            
        return True
        
    except Exception as e:
        print_error(f"Error creando categorías: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_sample_products():
    """Crea productos de ejemplo"""
    print_header("CREANDO PRODUCTOS DE EJEMPLO")
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen productos
        existing_products = db.query(Product).count()
        
        if existing_products == 0:
            # Obtener categorías
            categories = {cat.name: cat.id for cat in db.query(Category).all()}
            
            products = [
                # Suplementos
                Product(
                    category_id=categories.get("Suplementos"),
                    name="Proteína Whey Premium",
                    description="Proteína de suero de alta calidad, sabor vainilla",
                    barcode="7891234567890",
                    sku="PROT-WHY-VAN-1KG",
                    current_cost=85000,
                    selling_price=120000,
                    current_stock=25,
                    min_stock=5,
                    max_stock=50,
                    unit_of_measure="kg",
                    weight_per_unit=1.0,
                    status="active"
                ),
                Product(
                    category_id=categories.get("Suplementos"),
                    name="Creatina Monohidrato",
                    description="Creatina pura para aumentar fuerza y masa muscular",
                    barcode="7891234567891",
                    sku="CREAT-MONO-300G",
                    current_cost=35000,
                    selling_price=50000,
                    current_stock=30,
                    min_stock=10,
                    max_stock=60,
                    unit_of_measure="gramos",
                    weight_per_unit=300,
                    status="active"
                ),
                # Bebidas
                Product(
                    category_id=categories.get("Bebidas"),
                    name="Bebida Energética Natural",
                    description="Bebida isotónica natural con electrolitos",
                    barcode="7891234567892",
                    sku="BEB-ENER-500ML",
                    current_cost=2500,
                    selling_price=4000,
                    current_stock=100,
                    min_stock=20,
                    max_stock=200,
                    unit_of_measure="ml",
                    weight_per_unit=500,
                    status="active"
                ),
                Product(
                    category_id=categories.get("Bebidas"),
                    name="Agua Purificada",
                    description="Agua purificada en botella de 500ml",
                    barcode="7891234567893",
                    sku="AGUA-PUR-500ML",
                    current_cost=800,
                    selling_price=1500,
                    current_stock=150,
                    min_stock=30,
                    max_stock=300,
                    unit_of_measure="ml",
                    weight_per_unit=500,
                    status="active"
                ),
                # Snacks
                Product(
                    category_id=categories.get("Snacks Saludables"),
                    name="Barra Proteica Chocolate",
                    description="Barra energética alta en proteína, sabor chocolate",
                    barcode="7891234567894",
                    sku="BAR-PROT-CHOC-60G",
                    current_cost=1800,
                    selling_price=3000,
                    current_stock=80,
                    min_stock=15,
                    max_stock=150,
                    unit_of_measure="gramos",
                    weight_per_unit=60,
                    status="active"
                ),
                # Accesorios
                Product(
                    category_id=categories.get("Accesorios"),
                    name="Guantes de Entrenamiento",
                    description="Guantes acolchados para levantamiento de pesas",
                    barcode="7891234567895",
                    sku="GUANT-ENTR-L",
                    current_cost=15000,
                    selling_price=25000,
                    current_stock=20,
                    min_stock=5,
                    max_stock=40,
                    unit_of_measure="unidad",
                    status="active"
                ),
                Product(
                    category_id=categories.get("Accesorios"),
                    name="Toalla Deportiva",
                    description="Toalla de microfibra absorbente para gimnasio",
                    barcode="7891234567896",
                    sku="TOAL-DEPORT-MED",
                    current_cost=8000,
                    selling_price=15000,
                    current_stock=35,
                    min_stock=10,
                    max_stock=70,
                    unit_of_measure="unidad",
                    status="active"
                )
            ]
            
            for product in products:
                db.add(product)
            
            db.commit()
            print_success(f"{len(products)} productos de ejemplo creados")
        else:
            print_info(f"Ya existen {existing_products} productos")
            
        return True
        
    except Exception as e:
        print_error(f"Error creando productos: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_device_config():
    """Crea configuración de dispositivos por defecto"""
    print_header("CREANDO CONFIGURACIÓN DE DISPOSITIVOS")
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existe configuración
        existing_devices = db.query(DeviceConfig).count()
        
        if existing_devices == 0:
            devices = [
                DeviceConfig(
                    device_name="Dispositivo Principal - Entrada",
                    device_ip="192.168.1.100",
                    device_port=4370,
                    device_id="MAIN_ENTRANCE_01",
                    device_type=DeviceType.INBIO_PANEL,
                    is_active=True,
                    auto_sync=True,
                    sync_interval=300,
                    turnstile_enabled=True,
                    turnstile_relay_port=1,
                    access_duration=5
                ),
                DeviceConfig(
                    device_name="Dispositivo Secundario - Salida",
                    device_ip="192.168.1.101",
                    device_port=4370,
                    device_id="MAIN_EXIT_01",
                    device_type=DeviceType.ZKT_STANDALONE,
                    is_active=True,
                    auto_sync=True,
                    sync_interval=300,
                    turnstile_enabled=True,
                    turnstile_relay_port=1,
                    access_duration=3
                )
            ]
            
            for device in devices:
                db.add(device)
            
            db.commit()
            print_success(f"{len(devices)} dispositivos configurados")
        else:
            print_info(f"Ya existen {existing_devices} dispositivos configurados")
            
        return True
        
    except Exception as e:
        print_error(f"Error configurando dispositivos: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def print_credentials():
    """Imprime las credenciales de acceso"""
    print_header("CREDENCIALES DE ACCESO")
    
    print("🔐 Usuarios creados:")
    print("   👤 Administrador:")
    print("      📧 Email: admin@gym.com")
    print("      🔑 Contraseña: admin123")
    print()
    print("   👤 Gerente:")
    print("      📧 Email: manager@gym.com")
    print("      🔑 Contraseña: manager123")
    print()
    print("   👤 Entrenador:")
    print("      📧 Email: trainer@gym.com")
    print("      🔑 Contraseña: trainer123")
    print()
    print("   👤 Recepcionista:")
    print("      📧 Email: receptionist@gym.com")
    print("      🔑 Contraseña: reception123")
    print()
    print("   👤 Miembro de ejemplo:")
    print("      📧 Email: member@gym.com")
    print("      🔑 Contraseña: member123")

def main():
    """Función principal del script"""
    print_header("INSTALACIÓN COMPLETA DE ESQUEMAS DE BASE DE DATOS")
    print("Este script instalará todos los esquemas necesarios para el sistema del gimnasio")
    
    success_count = 0
    total_steps = 6
    
    # Paso 1: Crear tablas
    if create_all_tables():
        success_count += 1
    
    # Paso 2: Crear usuarios por defecto
    if create_default_users():
        success_count += 1
    
    # Paso 3: Crear planes de membresía
    if create_membership_plans():
        success_count += 1
    
    # Paso 4: Crear categorías de productos
    if create_product_categories():
        success_count += 1
    
    # Paso 5: Crear productos de ejemplo
    if create_sample_products():
        success_count += 1
    
    # Paso 6: Configurar dispositivos
    if create_device_config():
        success_count += 1
    
    # Resumen final
    print_header("RESUMEN DE INSTALACIÓN")
    
    if success_count == total_steps:
        print_success(f"¡Instalación completada exitosamente! ({success_count}/{total_steps} pasos)")
        print_success("Todos los esquemas de base de datos han sido instalados correctamente")
        print_credentials()
        
        print("\n🚀 Próximos pasos:")
        print("   1. Verificar la conexión a la base de datos")
        print("   2. Configurar las IPs de los dispositivos ZKTeco")
        print("   3. Probar el login con las credenciales proporcionadas")
        print("   4. Configurar los planes de membresía según sus necesidades")
        
    else:
        print_error(f"Instalación parcial: {success_count}/{total_steps} pasos completados")
        print("⚠️  Revise los errores anteriores y ejecute el script nuevamente")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
