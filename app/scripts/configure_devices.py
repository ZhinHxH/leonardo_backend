"""
Script para configurar dispositivos ZKTeco y talanquera
"""
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.fingerprint import DeviceConfig
from app.services.turnstile_service import TurnstileService

def configure_default_devices():
    """Configura dispositivos por defecto"""
    db = next(get_db())
    
    try:
        # Configurar panel inBIO principal
        inbio_device = DeviceConfig(
            device_name="inBIO Principal",
            device_ip="192.168.1.100",
            device_port=4370,
            device_id="INBIO001",
            is_active=True,
            auto_sync=True,
            sync_interval=300,
            turnstile_enabled=True,
            turnstile_relay_port=1,
            access_duration=5
        )
        
        # Verificar si ya existe
        existing = db.query(DeviceConfig).filter(
            DeviceConfig.device_ip == inbio_device.device_ip
        ).first()
        
        if not existing:
            db.add(inbio_device)
            print("✅ Panel inBIO configurado")
        else:
            print("ℹ️  Panel inBIO ya existe")
        
        # Configurar panel inBIO secundario (opcional)
        inbio_device_2 = DeviceConfig(
            device_name="inBIO Secundario",
            device_ip="192.168.1.101",
            device_port=4370,
            device_id="INBIO002",
            is_active=False,  # Inactivo por defecto
            auto_sync=False,
            sync_interval=300,
            turnstile_enabled=False,
            turnstile_relay_port=2,
            access_duration=5
        )
        
        existing_2 = db.query(DeviceConfig).filter(
            DeviceConfig.device_ip == inbio_device_2.device_ip
        ).first()
        
        if not existing_2:
            db.add(inbio_device_2)
            print("✅ Panel inBIO secundario configurado")
        else:
            print("ℹ️  Panel inBIO secundario ya existe")
        
        db.commit()
        print("✅ Configuración de dispositivos completada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando dispositivos: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_turnstile_connection():
    """Prueba la conexión con la talanquera"""
    print("\n🔧 Probando conexión con talanquera...")
    
    # Configuración para relé IP (ajustar según tu hardware)
    turnstile_service = TurnstileService(
        connection_type="relay",
        relay_ip="192.168.1.102",  # IP del relé
        relay_port=1
    )
    
    # Probar conexión
    if turnstile_service.test_connection():
        print("✅ Conexión con talanquera exitosa")
        
        # Probar apertura (solo por 1 segundo para prueba)
        result = turnstile_service.grant_access("TEST", 1)
        if result["success"]:
            print("✅ Prueba de apertura de talanquera exitosa")
        else:
            print(f"❌ Error en prueba de apertura: {result['message']}")
    else:
        print("❌ No se pudo conectar con la talanquera")
        print("💡 Verifica la IP del relé y la configuración de red")

def show_device_configuration():
    """Muestra la configuración actual de dispositivos"""
    db = next(get_db())
    
    try:
        devices = db.query(DeviceConfig).all()
        
        if not devices:
            print("❌ No hay dispositivos configurados")
            return
        
        print("\n📱 Dispositivos configurados:")
        print("-" * 80)
        
        for device in devices:
            status = "🟢 Activo" if device.is_active else "🔴 Inactivo"
            turnstile = "✅ Habilitada" if device.turnstile_enabled else "❌ Deshabilitada"
            
            print(f"Nombre: {device.device_name}")
            print(f"IP: {device.device_ip}:{device.device_port}")
            print(f"ID: {device.device_id}")
            print(f"Estado: {status}")
            print(f"Talanquera: {turnstile}")
            print(f"Última conexión: {device.last_connection or 'Nunca'}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Error mostrando configuración: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Configurando sistema de control de acceso...")
    
    # Configurar dispositivos
    configure_default_devices()
    
    # Mostrar configuración
    show_device_configuration()
    
    # Probar talanquera (opcional)
    test_connection = input("\n¿Probar conexión con talanquera? (s/n): ").lower()
    if test_connection == 's':
        test_turnstile_connection()
    
    print("\n✅ Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Ajusta las IPs de los dispositivos en la base de datos")
    print("2. Configura la IP del relé de la talanquera")
    print("3. Prueba la conexión con los dispositivos ZKTeco")
    print("4. Realiza pruebas de enrolamiento y verificación")
