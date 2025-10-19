"""
Script para descargar e instalar SDKs oficiales de ZKTeco
"""
import os
import sys
import requests
import zipfile
import platform
from pathlib import Path

def download_file(url, filename):
    """Descarga un archivo desde una URL"""
    try:
        print(f"📥 Descargando {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ {filename} descargado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error descargando {filename}: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extrae un archivo ZIP"""
    try:
        print(f"📦 Extrayendo {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✅ {zip_path} extraído exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error extrayendo {zip_path}: {e}")
        return False

def setup_zkfinger_sdk():
    """Configura ZKFinger SDK"""
    print("🔧 Configurando ZKFinger SDK...")
    
    # URLs de descarga (estas son URLs de ejemplo, necesitarás las reales)
    sdk_urls = {
        "windows": "https://www.zkteco.com/downloads/ZKFinger_SDK_Windows.zip",
        "linux": "https://www.zkteco.com/downloads/ZKFinger_SDK_Linux.zip"
    }
    
    # Determinar sistema operativo
    system = platform.system().lower()
    if system == "windows":
        sdk_url = sdk_urls["windows"]
        sdk_filename = "ZKFinger_SDK_Windows.zip"
    else:
        sdk_url = sdk_urls["linux"]
        sdk_filename = "ZKFinger_SDK_Linux.zip"
    
    # Crear directorio para SDKs
    sdk_dir = Path("sdk")
    sdk_dir.mkdir(exist_ok=True)
    
    # Descargar SDK
    if download_file(sdk_url, sdk_filename):
        # Extraer SDK
        extract_to = sdk_dir / "zkfinger"
        extract_to.mkdir(exist_ok=True)
        
        if extract_zip(sdk_filename, extract_to):
            print("✅ ZKFinger SDK configurado correctamente")
            
            # Limpiar archivo ZIP
            os.remove(sdk_filename)
            
            return True
    
    return False

def create_sdk_guide():
    """Crea guía de instalación manual"""
    guide = """
# 📋 Guía de Instalación Manual de SDKs ZKTeco

## 1. Descargar SDKs desde ZKTeco

Ve a: https://www.zkteco.com/en/download_center

### SDKs Necesarios:
- **ZKFinger SDK Windows** (34.18MB) - Para dispositivos biométricos
- **ZKBio Time API** - Para sistemas de tiempo y asistencia
- **ZKBio CVSecurity API** - Para sistemas de seguridad integrales

## 2. Instalación de ZKFinger SDK

### Windows:
1. Descarga `ZKFinger SDK Windows` (rar, 34.18MB)
2. Extrae el archivo RAR
3. Ejecuta el instalador
4. Copia las DLLs a `C:\\Windows\\System32`

### Linux:
1. Descarga `ZKFinger SDK Linux` (zip, 10.36MB)
2. Extrae el archivo ZIP
3. Compila las librerías según las instrucciones
4. Instala las librerías en el sistema

## 3. Configuración del Entorno

### Variables de Entorno:
```bash
# Windows
set ZKFINGER_SDK_PATH=C:\\Program Files\\ZKTeco\\ZKFinger SDK

# Linux
export ZKFINGER_SDK_PATH=/usr/local/lib/zkfinger
```

## 4. Verificación de Instalación

Ejecuta el script de prueba:
```bash
python app/scripts/test_zkteco_sdk.py
```

## 5. Configuración de Paneles inBIO

1. Conecta el panel inBIO a la red
2. Configura IP estática (ej: 192.168.1.100)
3. Verifica conectividad: `ping 192.168.1.100`
4. Ejecuta configuración: `python app/scripts/configure_devices.py`

## 6. Pruebas de Conectividad

```python
from app.services.zkteco_service import ZKTecoService

# Probar conexión
service = ZKTecoService()
result = service.test_connection("192.168.1.100")
print(result)
```

## 📞 Soporte

- **Soporte Técnico ZKTeco**: service@zkteco.com
- **Ventas ZKTeco**: sales@zkteco.com
- **Documentación**: https://www.zkteco.com/en/download_center
"""
    
    with open("SDK_INSTALLATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("📝 Guía de instalación creada: SDK_INSTALLATION_GUIDE.md")

def main():
    """Función principal"""
    print("🚀 Configurando SDKs oficiales de ZKTeco...")
    print("=" * 60)
    
    # Crear guía de instalación
    create_sdk_guide()
    
    print("\n📋 Instrucciones:")
    print("1. Ve a: https://www.zkteco.com/en/download_center")
    print("2. Descarga los SDKs necesarios:")
    print("   - ZKFinger SDK Windows (34.18MB)")
    print("   - ZKBio Time API")
    print("   - ZKBio CVSecurity API")
    print("3. Sigue la guía en: SDK_INSTALLATION_GUIDE.md")
    print("4. Ejecuta: python app/scripts/test_zkteco_sdk.py")
    
    print("\n✅ Configuración completada!")
    print("📖 Revisa SDK_INSTALLATION_GUIDE.md para instrucciones detalladas")

if __name__ == "__main__":
    main()









