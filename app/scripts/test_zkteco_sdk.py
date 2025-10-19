"""
Script de prueba para SDK oficial de ZKTeco
"""
import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.services.zkteco_official_service import ZKTecoOfficialSDK, ZKTecoOfficialService
from app.core.database import get_db

def test_sdk_loading():
    """Prueba la carga del SDK"""
    print("🧪 Probando carga del SDK oficial de ZKTeco...")
    
    try:
        device = ZKTecoOfficialSDK("192.168.1.100")
        print("✅ SDK cargado correctamente")
        
        # Verificar si se cargó el SDK real o la implementación simulada
        if device.lib:
            print("✅ SDK oficial de ZKTeco detectado")
        else:
            print("⚠️  Usando implementación simulada (SDK no encontrado)")
        
        return True
    except Exception as e:
        print(f"❌ Error cargando SDK: {e}")
        return False

def test_device_connection(ip="192.168.1.100", port=4370):
    """Prueba la conexión con el dispositivo"""
    print(f"🔌 Probando conexión con dispositivo en {ip}:{port}...")
    
    try:
        device = ZKTecoOfficialSDK(ip, port)
        
        if device.connect():
            print("✅ Conexión exitosa")
            
            # Obtener información del dispositivo
            info = device.get_device_info()
            print(f"📋 Información del dispositivo:")
            for key, value in info.items():
                print(f"   {key}: {value}")
            
            device.disconnect()
            return True
        else:
            print("❌ No se pudo conectar al dispositivo")
            print("💡 Verifica:")
            print("   - IP del dispositivo")
            print("   - Conectividad de red")
            print("   - Puerto (por defecto 4370)")
            return False
            
    except Exception as e:
        print(f"❌ Error en conexión: {e}")
        return False

def test_fingerprint_operations(ip="192.168.1.100"):
    """Prueba operaciones de huellas dactilares"""
    print("👆 Probando operaciones de huellas dactilares...")
    
    try:
        device = ZKTecoOfficialSDK(ip)
        
        if device.connect():
            print("✅ Conectado para pruebas de huellas")
            
            # Probar enrolamiento (simulado)
            print("📝 Probando enrolamiento...")
            enroll_result = device.enroll_fingerprint(123, 0)
            print(f"   Resultado: {'✅ Éxito' if enroll_result else '❌ Fallo'}")
            
            # Probar verificación (simulada)
            print("🔍 Probando verificación...")
            verify_result = device.verify_fingerprint(123)
            print(f"   Resultado: {verify_result}")
            
            # Probar apertura de puerta (simulada)
            print("🚪 Probando apertura de puerta...")
            door_result = device.open_door(1, 3)
            print(f"   Resultado: {'✅ Éxito' if door_result else '❌ Fallo'}")
            
            device.disconnect()
            return True
        else:
            print("❌ No se pudo conectar para pruebas de huellas")
            return False
            
    except Exception as e:
        print(f"❌ Error en pruebas de huellas: {e}")
        return False

def test_service_integration():
    """Prueba la integración con el servicio"""
    print("🔧 Probando integración con servicio...")
    
    try:
        db = next(get_db())
        service = ZKTecoOfficialService(db)
        
        # Probar estado del dispositivo
        print("📊 Probando estado del dispositivo...")
        status = service.get_device_status("192.168.1.100")
        print(f"   Estado: {status}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        return False

def show_installation_guide():
    """Muestra guía de instalación"""
    print("\n📋 Guía de Instalación del SDK Oficial:")
    print("=" * 50)
    print("1. Ve a: https://www.zkteco.com/en/download_center")
    print("2. Descarga 'ZKFinger SDK Windows' (34.18MB)")
    print("3. Extrae e instala el SDK")
    print("4. Copia las DLLs a C:\\Windows\\System32")
    print("5. Ejecuta este script nuevamente")
    print("\n📖 Para más detalles, revisa: SDK_INSTALLATION_GUIDE.md")

def main():
    """Función principal"""
    print("🚀 Pruebas del SDK Oficial de ZKTeco")
    print("=" * 50)
    
    # Prueba 1: Carga del SDK
    sdk_loaded = test_sdk_loading()
    
    if not sdk_loaded:
        print("\n❌ SDK no disponible")
        show_installation_guide()
        return
    
    # Prueba 2: Conexión con dispositivo
    print("\n" + "=" * 50)
    device_ip = input("Ingresa la IP del dispositivo ZKTeco (Enter para 192.168.1.100): ").strip()
    if not device_ip:
        device_ip = "192.168.1.100"
    
    connection_ok = test_device_connection(device_ip)
    
    if connection_ok:
        # Prueba 3: Operaciones de huellas
        print("\n" + "=" * 50)
        test_fingerprint_operations(device_ip)
        
        # Prueba 4: Integración con servicio
        print("\n" + "=" * 50)
        test_service_integration()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas!")
    
    if not connection_ok:
        print("\n💡 Si no puedes conectar:")
        print("   - Verifica la IP del dispositivo")
        print("   - Asegúrate de que esté en la misma red")
        print("   - Revisa que el dispositivo esté encendido")
        print("   - Consulta la documentación del dispositivo")

if __name__ == "__main__":
    main()









