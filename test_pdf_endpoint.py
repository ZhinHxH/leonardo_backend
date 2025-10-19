#!/usr/bin/env python3
"""
Script para probar el endpoint de PDF del cierre de caja
"""

import requests
import json

# Configuración
BASE_URL = "http://127.0.0.1:8000"
CLOSURE_ID = 1

def test_pdf_endpoint():
    """Prueba el endpoint de PDF del cierre de caja"""
    
    print(f"🧪 Probando endpoint de PDF para cierre de caja ID: {CLOSURE_ID}")
    
    # URL del endpoint
    url = f"{BASE_URL}/api/cash-closures/{CLOSURE_ID}/pdf"
    print(f"📡 URL: {url}")
    
    try:
        # Hacer la petición
        response = requests.get(url, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Endpoint funcionando correctamente")
            print(f"📄 Content-Type: {response.headers.get('content-type')}")
            print(f"📏 Content-Length: {response.headers.get('content-length')}")
            
            # Verificar que es un PDF
            if 'application/pdf' in response.headers.get('content-type', ''):
                print("✅ Respuesta es un PDF válido")
            else:
                print("⚠️  La respuesta no es un PDF")
                
        elif response.status_code == 404:
            print("❌ Error 404: Endpoint no encontrado")
            print("🔍 Posibles causas:")
            print("   - El servidor no está corriendo")
            print("   - El endpoint no está registrado")
            print("   - El cierre de caja no existe")
            
        elif response.status_code == 401:
            print("❌ Error 401: No autorizado")
            print("🔍 Necesitas autenticarte primero")
            
        elif response.status_code == 403:
            print("❌ Error 403: Sin permisos")
            print("🔍 No tienes permisos para acceder a este recurso")
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: El servidor no está corriendo")
        print("🔍 Asegúrate de que el servidor esté corriendo en http://127.0.0.1:8000")
        
    except requests.exceptions.Timeout:
        print("❌ Error de timeout: La petición tardó demasiado")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_server_status():
    """Prueba si el servidor está funcionando"""
    
    print("🔍 Verificando estado del servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
            return True
        else:
            print(f"⚠️  Servidor respondió con código: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Servidor no está corriendo")
        return False
        
    except Exception as e:
        print(f"❌ Error verificando servidor: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del endpoint de PDF")
    print("=" * 50)
    
    # Verificar servidor
    if test_server_status():
        print("\n" + "=" * 50)
        test_pdf_endpoint()
    else:
        print("\n❌ No se puede probar el endpoint sin servidor")
        print("💡 Ejecuta: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
