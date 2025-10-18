# 🔐 Sistema de Control de Acceso con Paneles inBIO de ZKTeco

## 📋 Descripción General

Este sistema integra paneles **inBIO** de ZKTeco con tu sistema de gestión de gimnasio para controlar el acceso mediante huellas dactilares. Solo permite el acceso a usuarios con membresía activa y huella registrada.

### 🎯 Paneles Compatibles
- **inBIO 160** - Panel compacto con lector de huellas
- **inBIO 260** - Panel con pantalla táctil y lector de huellas  
- **inBIO 460** - Panel avanzado con múltiples opciones de autenticación

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Panel inBIO   │    │   Sistema API    │    │   Talanquera    │
│   ZKTeco        │◄──►│   FastAPI        │◄──►│   (Relé IP)     │
│   (PULL SDK)    │    │   + Base Datos   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Enrolamiento  │    │   Validación     │    │   Control de    │
│   de Huellas    │    │   de Membresía   │    │   Acceso        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Instalación y Configuración

### 1. Instalar SDK de ZKTeco para inBIO

```bash
cd Backend
python app/scripts/install_inbio_sdk.py
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Crear Tablas de Base de Datos

```bash
python app/scripts/create_fingerprint_tables.py
```

### 4. Configurar Paneles inBIO

```bash
python app/scripts/configure_devices.py
```

## 🔧 Configuración de Hardware

### Paneles inBIO ZKTeco
- **IP por defecto**: 192.168.1.100
- **Puerto**: 4370
- **Protocolo**: PULL SDK (TCP/IP)
- **SDK requerido**: PULL SDK de ZKTeco

### Talanquera (Relé IP)
- **IP por defecto**: 192.168.1.102
- **Puerto**: 80
- **Tipo**: Relé IP controlado por HTTP

### Configuración de Red
1. Conecta el dispositivo ZKTeco a la red local
2. Configura IP estática para el dispositivo
3. Configura IP estática para el relé de la talanquera
4. Asegúrate de que el servidor pueda comunicarse con ambos dispositivos

## 📊 Modelos de Datos

### Fingerprint
```python
- id: Identificador único
- user_id: ID del usuario
- fingerprint_template: Template de la huella
- fingerprint_id: ID en el dispositivo ZKTeco
- finger_index: Índice del dedo (0-9)
- quality_score: Calidad de la huella (0-100)
- status: Estado (active, inactive, pending, expired)
- enrolled_at: Fecha de enrolamiento
- last_used: Último uso
- expires_at: Fecha de expiración
```

### AccessEvent
```python
- id: Identificador único
- user_id: ID del usuario
- fingerprint_id: ID de la huella
- event_type: Tipo de evento
- access_method: Método de acceso
- access_granted: Si se concedió acceso
- denial_reason: Razón de denegación
- device_ip: IP del dispositivo
- event_time: Timestamp del evento
```

### DeviceConfig
```python
- id: Identificador único
- device_name: Nombre del dispositivo
- device_ip: IP del dispositivo
- device_port: Puerto del dispositivo
- device_id: ID único del dispositivo
- is_active: Si está activo
- turnstile_enabled: Si controla talanquera
- turnstile_relay_port: Puerto del relé
- access_duration: Duración de apertura (segundos)
```

## 🔌 API Endpoints

### Enrolamiento de Huellas
```http
POST /api/fingerprint/enroll
{
    "user_id": 123,
    "device_ip": "192.168.1.100",
    "finger_index": 0
}
```

### Verificación de Acceso
```http
POST /api/fingerprint/verify-access
{
    "device_ip": "192.168.1.100",
    "user_id": 123
}
```

### Obtener Huellas de Usuario
```http
GET /api/fingerprint/user/{user_id}
```

### Eventos de Acceso
```http
GET /api/fingerprint/access-events?user_id=123&limit=50
```

### Estado del Dispositivo
```http
GET /api/fingerprint/device/{device_ip}/status
```

## 🔄 Flujo de Trabajo

### 1. Enrolamiento de Usuario
1. Usuario debe tener membresía activa
2. Administrador inicia proceso de enrolamiento
3. Usuario coloca dedo en sensor ZKTeco
4. Sistema valida calidad de huella
5. Huella se almacena en dispositivo y base de datos

### 2. Verificación de Acceso
1. Usuario coloca dedo en sensor
2. Dispositivo ZKTeco identifica usuario
3. Sistema verifica membresía activa
4. Si es válido: abre talanquera
5. Si no es válido: registra evento de denegación

### 3. Control de Talanquera
1. Sistema envía comando de apertura
2. Relé IP activa talanquera
3. Talanquera permanece abierta por tiempo configurado
4. Se registra evento de acceso

## 🛠️ Configuración Avanzada

### Tipos de Conexión de Talanquera

#### 1. Relé IP (Recomendado)
```python
turnstile_service = TurnstileService(
    connection_type="relay",
    relay_ip="192.168.1.102",
    relay_port=1
)
```

#### 2. Puerto Serie
```python
turnstile_service = TurnstileService(
    connection_type="serial",
    port="COM1",
    baudrate=9600
)
```

#### 3. TCP/IP
```python
turnstile_service = TurnstileService(
    connection_type="tcp",
    host="192.168.1.103",
    port=8080
)
```

### Configuración de Dispositivos Múltiples

```python
# Dispositivo principal
device_1 = DeviceConfig(
    device_name="Entrada Principal",
    device_ip="192.168.1.100",
    device_id="ZK001",
    turnstile_enabled=True
)

# Dispositivo secundario
device_2 = DeviceConfig(
    device_name="Entrada Secundaria",
    device_ip="192.168.1.101",
    device_id="ZK002",
    turnstile_enabled=False
)
```

## 🔍 Monitoreo y Logs

### Eventos Registrados
- ✅ Acceso concedido
- ❌ Acceso denegado (membresía expirada)
- ❌ Acceso denegado (huella no encontrada)
- ❌ Acceso denegado (huella no coincide)
- ❌ Error de dispositivo
- ❌ Error de talanquera

### Consultas Útiles

```sql
-- Usuarios con más accesos
SELECT u.name, COUNT(ae.id) as access_count
FROM users u
JOIN access_events ae ON u.id = ae.user_id
WHERE ae.access_granted = true
GROUP BY u.id, u.name
ORDER BY access_count DESC;

-- Eventos de denegación por razón
SELECT denial_reason, COUNT(*) as count
FROM access_events
WHERE access_granted = false
GROUP BY denial_reason;

-- Actividad por dispositivo
SELECT device_ip, COUNT(*) as events
FROM access_events
WHERE event_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY device_ip;
```

## 🚨 Solución de Problemas

### Problemas Comunes

#### 1. No se puede conectar al dispositivo ZKTeco
- ✅ Verificar IP y puerto del dispositivo
- ✅ Verificar conectividad de red
- ✅ Verificar que el dispositivo esté encendido
- ✅ Verificar firewall del servidor

#### 2. Talanquera no se abre
- ✅ Verificar IP del relé
- ✅ Verificar configuración del relé
- ✅ Probar comando manual de apertura
- ✅ Verificar alimentación de la talanquera

#### 3. Huellas no se reconocen
- ✅ Verificar calidad del enrolamiento
- ✅ Limpiar sensor de huellas
- ✅ Re-enrolar huella si es necesario
- ✅ Verificar configuración de tolerancia

### Comandos de Diagnóstico

```bash
# Probar conectividad con dispositivo
ping 192.168.1.100

# Probar puerto del dispositivo
telnet 192.168.1.100 4370

# Verificar estado del servicio
python -c "from app.services.fingerprint_service import ZKTecoDevice; d = ZKTecoDevice('192.168.1.100'); print(d.connect())"
```

## 📈 Optimizaciones

### Rendimiento
- Usar conexiones persistentes cuando sea posible
- Implementar cache para consultas frecuentes
- Optimizar consultas de base de datos
- Usar índices en campos de búsqueda frecuente

### Seguridad
- Encriptar templates de huellas
- Implementar logs de auditoría
- Usar HTTPS para comunicación
- Validar todas las entradas de usuario

### Escalabilidad
- Implementar balanceador de carga para múltiples dispositivos
- Usar base de datos distribuida si es necesario
- Implementar cache distribuido
- Monitorear uso de recursos

## 🔮 Funcionalidades Futuras

- [ ] Reconocimiento facial adicional
- [ ] Tarjetas RFID como respaldo
- [ ] Notificaciones por WhatsApp/Email
- [ ] Dashboard en tiempo real
- [ ] Reportes avanzados
- [ ] Integración con cámaras de seguridad
- [ ] Control de horarios de acceso
- [ ] Sistema de invitados temporales

## 📞 Soporte

Para soporte técnico o consultas sobre la implementación:

1. Revisar logs del sistema
2. Verificar configuración de red
3. Probar dispositivos individualmente
4. Consultar documentación de ZKTeco
5. Contactar soporte técnico si es necesario

---

**¡Sistema listo para usar! 🎉**

Este sistema te permitirá controlar el acceso a tu gimnasio de manera eficiente y segura, sin necesidad de software adicional costoso.
