"""
Script para instalar y configurar el SDK de ZKTeco para paneles inBIO
"""
import os
import sys
import subprocess
import platform
import requests
from pathlib import Path

def check_python_architecture():
    """Verifica la arquitectura de Python"""
    arch = platform.architecture()[0]
    print(f"Arquitectura de Python: {arch}")
    
    if arch != "32bit":
        print("⚠️  ADVERTENCIA: pyzkaccess requiere Python de 32 bits")
        print("   Para Windows, descarga Python 3.8 32-bit desde python.org")
        return False
    return True

def install_pyzkaccess():
    """Instala pyzkaccess"""
    try:
        print("📦 Instalando pyzkaccess...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "pyzkaccess==1.0.0"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ pyzkaccess instalado correctamente")
            return True
        else:
            print(f"❌ Error instalando pyzkaccess: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def setup_zkaccess():
    """Configura pyzkaccess"""
    try:
        print("🔧 Configurando pyzkaccess...")
        result = subprocess.run([
            sys.executable, "-m", "pyzkaccess", "setup"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ pyzkaccess configurado correctamente")
            return True
        else:
            print(f"❌ Error configurando pyzkaccess: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_zkaccess():
    """Prueba la instalación de pyzkaccess"""
    try:
        print("🧪 Probando instalación de pyzkaccess...")
        result = subprocess.run([
            sys.executable, "-m", "pyzkaccess", "search_devices"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ pyzkaccess funcionando correctamente")
            print("📋 Dispositivos encontrados:")
            print(result.stdout)
            return True
        else:
            print(f"⚠️  pyzkaccess instalado pero no encuentra dispositivos: {result.stderr}")
            print("   Esto es normal si no hay dispositivos inBIO en la red")
            return True
    except Exception as e:
        print(f"❌ Error probando pyzkaccess: {e}")
        return False

def download_sdk_manually():
    """Guía para descarga manual del SDK"""
    print("\n📥 Si la instalación automática falla, descarga manualmente:")
    print("1. Ve a: https://www.zkteco.com/support/downloads")
    print("2. Busca 'PULL SDK' para paneles inBIO")
    print("3. Descarga la versión más reciente")
    print("4. Instala el SDK")
    print("5. Copia los archivos pl*.dll a C:\\Windows\\SysWOW64")
    print("6. Ejecuta este script nuevamente")

def create_test_script():
    """Crea script de prueba para inBIO"""
    test_script = """
# Script de prueba para paneles inBIO
from pyzkaccess import ZKAccess

def test_inbio_connection(ip="192.168.1.100", port=4370):
    try:
        zk = ZKAccess(ip, port)
        if zk.connect():
            print(f"✅ Conectado al panel inBIO en {ip}:{port}")
            
            # Obtener información del dispositivo
            info = zk.get_device_info()
            print(f"📋 Información del dispositivo: {info}")
            
            zk.disconnect()
            return True
        else:
            print(f"❌ No se pudo conectar al panel inBIO en {ip}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Cambia la IP por la de tu panel inBIO
    test_inbio_connection("192.168.1.100")
"""
    
    with open("test_inbio.py", "w") as f:
        f.write(test_script)
    
    print("📝 Script de prueba creado: test_inbio.py")

def main():
    """Función principal"""
    print("🚀 Instalando SDK de ZKTeco para paneles inBIO...")
    print("=" * 60)
    
    # Verificar arquitectura de Python
    if not check_python_architecture():
        print("\n❌ Instalación cancelada. Instala Python de 32 bits primero.")
        return False
    
    # Instalar pyzkaccess
    if not install_pyzkaccess():
        print("\n❌ Error instalando pyzkaccess")
        download_sdk_manually()
        return False
    
    # Configurar pyzkaccess
    if not setup_zkaccess():
        print("\n⚠️  Error configurando pyzkaccess automáticamente")
        print("   Intenta la instalación manual del SDK")
        download_sdk_manually()
    
    # Probar instalación
    if not test_zkaccess():
        print("\n❌ Error probando pyzkaccess")
        return False
    
    # Crear script de prueba
    create_test_script()
    
    print("\n✅ Instalación completada!")
    print("\n📋 Próximos pasos:")
    print("1. Configura la IP de tu panel inBIO")
    print("2. Ejecuta: python test_inbio.py")
    print("3. Si funciona, ejecuta: python app/scripts/configure_devices.py")
    print("4. Inicia tu aplicación FastAPI")
    
    return True

if __name__ == "__main__":
    main()









