# Sistema de Cierre de Caja

## 📋 Descripción

El sistema de cierre de caja permite a los usuarios registrar el cierre de su turno, comparando las ventas del sistema con el conteo físico de efectivo y otros métodos de pago. Incluye reportes detallados y análisis de diferencias.

## 🏗️ Arquitectura

### Backend

#### Modelos
- **`CashClosure`** (`app/models/cash_closure.py`): Modelo principal para cierres de caja
- **`CashClosureStatus`**: Estados del cierre (pending, completed, reviewed, cancelled)
- **`PaymentMethodType`**: Tipos de métodos de pago

#### Servicios
- **`CashClosureService`** (`app/services/cash_closure_service.py`): Lógica de negocio
  - Crear cierres de caja
  - Calcular diferencias automáticamente
  - Generar reportes
  - Obtener resúmenes de turno

#### Controladores
- **`cash_closure_controller.py`**: Endpoints REST
  - `POST /cash-closures/`: Crear cierre
  - `GET /cash-closures/`: Listar cierres
  - `GET /cash-closures/{id}`: Obtener cierre específico
  - `PUT /cash-closures/{id}`: Actualizar cierre
  - `GET /cash-closures/reports/summary`: Reporte general
  - `GET /cash-closures/reports/daily-summary`: Resumen diario

### Frontend

#### Componentes
- **`CashClosure`** (`src/components/CashClosure/index.tsx`): Modal de cierre de caja
- **`cash-closures.tsx`** (`src/pages/reports/cash-closures.tsx`): Reportes de cierres

#### Servicios
- **`cash-closure.ts`** (`src/services/cash-closure.ts`): API client para cierres

## 🚀 Funcionalidades

### 1. Cierre de Caja
- **Resumen automático** de ventas del turno
- **Conteo físico** de efectivo y otros métodos de pago
- **Cálculo automático** de diferencias
- **Notas** sobre discrepancias
- **Validación de roles** (solo ADMIN, MANAGER, RECEPTIONIST)

### 2. Métodos de Pago Soportados
- 💵 **Efectivo** (Cash)
- 📱 **Nequi**
- 🏦 **Bancolombia**
- 📱 **Daviplata**
- 💳 **Tarjeta**
- 🔄 **Transferencia**

### 3. Reportes y Análisis
- **Historial completo** de cierres
- **Resumen por usuario**
- **Análisis de diferencias**
- **Reportes por período**
- **Estadísticas diarias**

## 📊 Estructura de Datos

### CashClosure Model
```python
class CashClosure:
    # Información básica
    id: int
    user_id: int
    shift_date: datetime
    shift_start: datetime
    shift_end: datetime
    
    # Resumen de ventas
    total_sales: float
    total_products_sold: int
    total_memberships_sold: int
    total_daily_access_sold: int
    
    # Desglose por método de pago (ventas del sistema)
    cash_sales: float
    nequi_sales: float
    bancolombia_sales: float
    daviplata_sales: float
    card_sales: float
    transfer_sales: float
    
    # Conteo físico
    cash_counted: float
    nequi_counted: float
    bancolombia_counted: float
    daviplata_counted: float
    card_counted: float
    transfer_counted: float
    
    # Diferencias calculadas automáticamente
    cash_difference: float
    nequi_difference: float
    # ... etc para cada método
    
    # Estado y notas
    status: CashClosureStatus
    notes: str
    discrepancies_notes: str
```

## 🔧 Instalación

### 1. Crear Tablas
```bash
cd Backend
python app/scripts/create_cash_closure_tables.py
```

### 2. Verificar Instalación
```bash
# Verificar que las tablas se crearon
python -c "
from app.core.database import engine
from app.models.cash_closure import CashClosure
print('Tablas:', CashClosure.metadata.tables.keys())
"
```

## 🎯 Uso del Sistema

### 1. Acceder al Cierre de Caja
1. Ir a **Ventas > Historial de Ventas**
2. Hacer clic en **"Cierre de Caja"**
3. El sistema cargará automáticamente el resumen del turno

### 2. Completar el Cierre
1. **Revisar resumen** de ventas del sistema
2. **Ingresar conteo físico** para cada método de pago
3. **Revisar diferencias** calculadas automáticamente
4. **Agregar notas** si hay discrepancias
5. **Guardar** el cierre

### 3. Ver Reportes
1. Ir a **Reportes > Cierres de Caja**
2. **Filtrar por fechas** si es necesario
3. **Ver detalles** de cualquier cierre
4. **Analizar diferencias** y tendencias

## 🔐 Seguridad y Permisos

### Roles Permitidos
- **ADMIN**: Acceso completo a todos los cierres y reportes
- **MANAGER**: Acceso completo a todos los cierres y reportes
- **RECEPTIONIST**: Puede crear cierres, ver solo sus propios cierres

### Validaciones
- Solo usuarios autorizados pueden crear cierres
- Los cierres se asocian automáticamente al usuario actual
- Los reportes requieren permisos de administrador o gerente

## 📈 Análisis de Diferencias

### Cálculo Automático
```typescript
// Para cada método de pago
difference = counted_amount - system_amount

// Si hay diferencia significativa (>$0.01)
// Se genera nota automática
```

### Tipos de Diferencias
- **✅ Sin diferencias**: Conteo coincide con sistema
- **⚠️ Diferencias menores**: < $100
- **❌ Diferencias mayores**: ≥ $100

## 🚨 Alertas y Notificaciones

### Diferencias Detectadas
- **Chip de color** según magnitud de diferencia
- **Notas automáticas** sobre discrepancias
- **Iconos visuales** para identificación rápida

### Estados del Cierre
- **🟡 Pending**: Cierre creado, pendiente de revisión
- **🟢 Completed**: Cierre completado
- **🔵 Reviewed**: Cierre revisado por supervisor
- **🔴 Cancelled**: Cierre cancelado

## 📋 Reportes Disponibles

### 1. Resumen General
- Total de cierres en período
- Total de ventas vs total contado
- Número de cierres con diferencias
- Promedio de diferencias

### 2. Análisis por Usuario
- Cierres por usuario
- Total de ventas por usuario
- Diferencias por usuario
- Rendimiento individual

### 3. Análisis Diario
- Cierres por día
- Ventas por día
- Diferencias por día
- Tendencias temporales

## 🔄 Flujo de Trabajo

### 1. Inicio de Turno
- Usuario inicia sesión
- Sistema registra hora de inicio
- Usuario realiza ventas normalmente

### 2. Cierre de Turno
- Usuario hace clic en "Cierre de Caja"
- Sistema calcula resumen automático
- Usuario ingresa conteo físico
- Sistema calcula diferencias
- Usuario revisa y guarda

### 3. Revisión (Opcional)
- Supervisor puede revisar cierres
- Marcar como "reviewed"
- Agregar comentarios adicionales

## 🛠️ Mantenimiento

### Limpieza de Datos
```sql
-- Eliminar cierres antiguos (más de 1 año)
DELETE FROM cash_closures 
WHERE created_at < datetime('now', '-1 year');
```

### Backup de Datos
```bash
# Backup de tabla de cierres
sqlite3 gym_db.db ".backup cash_closures_backup.db"
```

## 🐛 Solución de Problemas

### Problemas Comunes

#### 1. Error al crear cierre
- **Causa**: Usuario sin permisos
- **Solución**: Verificar rol del usuario

#### 2. Diferencias no calculadas
- **Causa**: Datos de conteo faltantes
- **Solución**: Verificar que todos los campos estén completos

#### 3. Reportes vacíos
- **Causa**: Filtros de fecha incorrectos
- **Solución**: Verificar rango de fechas

### Logs y Debugging
```python
# Habilitar logs detallados
import logging
logging.getLogger('app.services.cash_closure_service').setLevel(logging.DEBUG)
```

## 📚 API Reference

### Endpoints Principales

#### Crear Cierre
```http
POST /api/cash-closures/
Content-Type: application/json

{
  "shift_date": "2024-01-15",
  "shift_start": "2024-01-15T08:00:00Z",
  "total_sales": 1500000,
  "cash_sales": 800000,
  "nequi_sales": 700000,
  "cash_counted": 800000,
  "nequi_counted": 700000,
  "notes": "Cierre normal del día"
}
```

#### Obtener Cierres
```http
GET /api/cash-closures/?start_date=2024-01-01&end_date=2024-01-31&page=1&per_page=50
```

#### Reporte de Cierres
```http
GET /api/cash-closures/reports/summary?start_date=2024-01-01&end_date=2024-01-31
```

## 🎉 Conclusión

El sistema de cierre de caja proporciona:

- ✅ **Control total** sobre el flujo de efectivo
- ✅ **Trazabilidad completa** de todas las transacciones
- ✅ **Análisis detallado** de diferencias y tendencias
- ✅ **Reportes profesionales** para toma de decisiones
- ✅ **Seguridad robusta** con validación de roles
- ✅ **Interfaz intuitiva** para uso diario

Este sistema es esencial para el control financiero del gimnasio y proporciona la transparencia necesaria para una gestión exitosa.
