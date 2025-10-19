# 🗄️ Scripts de Configuración de Base de Datos

Este directorio contiene scripts para configurar y mantener la base de datos del sistema de gimnasio.

## 📋 Scripts Disponibles

### 1. `install_database_schemas.py` - Instalación Completa
**Script principal para configuración completa del sistema**

```bash
cd Backend
python app/scripts/install_database_schemas.py
```

**¿Qué hace este script?**
- ✅ Crea todas las tablas de la base de datos
- ✅ Instala usuarios por defecto (admin, manager, trainer, etc.)
- ✅ Crea planes de membresía predefinidos
- ✅ Configura categorías de productos
- ✅ Agrega productos de ejemplo
- ✅ Configura dispositivos de control de acceso
- ✅ Proporciona credenciales de acceso

**Usuarios creados:**
- **Admin**: `admin@gym.com` / `admin123`
- **Manager**: `manager@gym.com` / `manager123`
- **Trainer**: `trainer@gym.com` / `trainer123`
- **Receptionist**: `receptionist@gym.com` / `reception123`
- **Member**: `member@gym.com` / `member123`

### 2. `create_tables_only.py` - Solo Esquemas
**Script ligero para crear solo las tablas**

```bash
cd Backend
python app/scripts/create_tables_only.py
```

**¿Qué hace este script?**
- ✅ Crea todas las tablas de la base de datos
- ❌ No agrega datos de ejemplo
- ❌ No crea usuarios por defecto

### 3. `init_db.py` - Usuarios Básicos
**Script existente para crear solo usuarios básicos**

```bash
cd Backend
python app/scripts/init_db.py
```

### 4. `create_clinical_tables.py` - Tablas Clínicas
**Script existente para tablas del sistema clínico**

```bash
cd Backend
python app/scripts/create_clinical_tables.py
```

## 🚀 Guía de Uso

### Primera Instalación (Recomendado)
Para una instalación completa desde cero:

```bash
cd Backend
python app/scripts/install_database_schemas.py
```

### Solo Crear Tablas
Si ya tienes datos y solo necesitas crear las tablas:

```bash
cd Backend
python app/scripts/create_tables_only.py
```

### Instalación por Módulos
Para instalar módulos específicos:

```bash
# Solo usuarios básicos
python app/scripts/init_db.py

# Solo sistema clínico
python app/scripts/create_clinical_tables.py
```

## 📊 Tablas Creadas

### 👥 Sistema de Usuarios
- `users` - Información de usuarios
- `memberships` - Membresías activas
- `attendances` - Registro de asistencias

### 🏥 Sistema Clínico
- `clinical_history` - Historial médico
- `user_goals` - Objetivos de usuarios
- `membership_plans` - Planes disponibles

### 🛒 Sistema de Inventario
- `categories` - Categorías de productos
- `products` - Inventario de productos
- `stock_movements` - Movimientos de stock
- `product_cost_history` - Historial de costos
- `inventory_reports` - Reportes generados

### 💰 Sistema de Ventas
- `sales` - Ventas realizadas
- `sale_items` - Detalles de ventas

### 🔐 Sistema de Acceso
- `fingerprints` - Huellas dactilares
- `access_events` - Eventos de acceso
- `device_configs` - Configuración de dispositivos

## ⚠️ Consideraciones Importantes

### Antes de Ejecutar
1. **Verificar conexión a BD**: Asegúrate de que la base de datos esté corriendo
2. **Configurar variables**: Revisa `app/core/config.py` para la configuración de BD
3. **Backup**: Si tienes datos existentes, haz un backup antes

### Después de Ejecutar
1. **Verificar credenciales**: Prueba el login con las credenciales proporcionadas
2. **Configurar dispositivos**: Actualiza las IPs de los dispositivos ZKTeco
3. **Personalizar planes**: Modifica los planes de membresía según tus necesidades
4. **Agregar productos**: Agrega tus productos específicos al inventario

## 🔧 Solución de Problemas

### Error de Conexión a BD
```bash
❌ Error: Can't connect to database
```
**Solución**: Verificar que la base de datos esté corriendo y la configuración sea correcta.

### Error de Permisos
```bash
❌ Error: Access denied for user
```
**Solución**: Verificar credenciales de base de datos en `config.py`.

### Tablas ya Existen
```bash
ℹ️ Los usuarios por defecto ya existen
```
**Esto es normal**: El script detecta datos existentes y no los duplica.

### Error de Importación
```bash
❌ Error importing models
```
**Solución**: Verificar que todas las dependencias estén instaladas:
```bash
pip install -r requirements.txt
```

## 📝 Logs y Debugging

Los scripts proporcionan salida detallada:
- ✅ Operaciones exitosas
- ℹ️ Información general
- ❌ Errores encontrados

Para debugging adicional, revisa:
- `app.log` - Log general de la aplicación
- `errors.log` - Log específico de errores

## 🔄 Actualización de Esquemas

Para actualizar esquemas existentes:

1. **Backup de datos importantes**
2. **Ejecutar script de actualización**
3. **Verificar integridad de datos**

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de error
2. Verifica la configuración de base de datos
3. Asegúrate de tener todas las dependencias instaladas
4. Consulta la documentación específica de cada módulo
