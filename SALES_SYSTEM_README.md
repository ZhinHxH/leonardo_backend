# 🛒 Sistema de Ventas Completo - Gimnasio Leonardo

## 📋 Descripción General

Sistema completo de ventas integrado con inventario y membresías, diseñado específicamente para gimnasios. Incluye interfaz POS optimizada, gestión de reversiones y seguimiento detallado de transacciones.

## 🚀 Características Principales

### ✅ **Punto de Venta (POS)**
- **Interfaz optimizada** para ventas rápidas
- **Búsqueda inteligente** de productos por nombre, SKU, código
- **Carrito dinámico** con cálculos automáticos
- **Múltiples métodos de pago** (Efectivo, Nequi, Bancolombia, Tarjeta)
- **Validación de stock** en tiempo real
- **Cálculo automático** de IVA, descuentos y cambio

### ✅ **Gestión de Inventario Integrada**
- **Actualización automática** de stock al vender
- **Control de disponibilidad** por producto
- **Movimientos de stock** registrados automáticamente
- **Alertas de stock bajo** integradas

### ✅ **Ventas de Membresías**
- **Integración completa** con planes de membresía
- **Activación automática** de membresías al vender
- **Gestión de clientes** requerida para membresías
- **Fechas de inicio y fin** calculadas automáticamente

### ✅ **Sistema de Reversión**
- **Reversión completa** de ventas (solo mismo día)
- **Reabastecimiento automático** de productos
- **Cancelación automática** de membresías creadas
- **Log de auditoría** completo con razones
- **Permisos restringidos** (solo admin/manager)

### ✅ **Historial y Reportes**
- **Historial completo** de todas las ventas
- **Filtros avanzados** por fecha, estado, vendedor
- **Detalles completos** de cada transacción
- **Paginación eficiente** para grandes volúmenes
- **Exportación de datos** (preparado)

## 🏗️ Arquitectura Técnica

### **Backend (FastAPI)**
```
📁 Backend/
├── app/models/sales.py          # Modelos de datos
├── app/services/sales_service.py # Lógica de negocio
├── app/routes/sales.py          # Endpoints API
└── app/controllers/             # Controladores
```

### **Frontend (Next.js + Material-UI)**
```
📁 Frontend/src/
├── pages/sales/
│   ├── index.tsx               # Dashboard principal
│   ├── pos.tsx                # Interfaz POS
│   └── history.tsx            # Historial de ventas
├── services/sales.ts          # Cliente API
└── components/                # Componentes reutilizables
```

### **Base de Datos (MySQL)**
```sql
-- Tablas principales
sales                 # Venta principal
sale_items           # Items de productos
membership_sales     # Items de membresías
sale_reversal_logs   # Log de reversiones
```

## 🔄 Flujo de Ventas

### **1. Venta de Productos**
```
1. Buscar producto → 2. Agregar al carrito → 3. Validar stock
4. Calcular totales → 5. Procesar pago → 6. Actualizar inventario
7. Generar recibo → 8. Registrar movimiento de stock
```

### **2. Venta de Membresías**
```
1. Seleccionar cliente → 2. Elegir plan → 3. Agregar al carrito
4. Calcular totales → 5. Procesar pago → 6. Crear membresía activa
7. Generar recibo → 8. Notificar activación
```

### **3. Reversión de Ventas**
```
1. Validar permisos → 2. Verificar tiempo (24h) → 3. Solicitar razón
4. Reabastecer productos → 5. Cancelar membresías → 6. Registrar log
7. Actualizar estado → 8. Notificar reversión
```

## 📊 Modelos de Datos

### **Sale (Venta Principal)**
```python
- id: int (PK)
- sale_number: str (único)
- customer_id: int (FK, opcional)
- seller_id: int (FK)
- sale_type: enum (product/membership/mixed)
- status: enum (pending/completed/cancelled/refunded)
- subtotal, tax_amount, discount_amount, total_amount: float
- payment_method: enum
- amount_paid, change_amount: float
- is_reversed: bool
- created_at, updated_at: datetime
```

### **SaleItem (Items de Productos)**
```python
- id: int (PK)
- sale_id: int (FK)
- product_id: int (FK)
- product_name, product_sku: str (snapshot)
- quantity: int
- unit_price, unit_cost: float (snapshot)
- discount_percentage: float
- line_total: float
```

### **MembershipSale (Items de Membresías)**
```python
- id: int (PK)
- sale_id: int (FK)
- membership_plan_id: int (FK)
- membership_id: int (FK, creada después)
- plan_name: str (snapshot)
- plan_duration_days: int
- plan_price: float
- membership_start_date, membership_end_date: datetime
```

## 🔐 Seguridad y Permisos

### **Roles y Accesos**
- **Admin**: Acceso completo, puede reversar ventas
- **Manager**: Acceso completo, puede reversar ventas
- **Receptionist**: Puede crear ventas, ver historial
- **Member**: Sin acceso al sistema de ventas

### **Validaciones**
- **Autenticación requerida** para todos los endpoints
- **Validación de stock** antes de vender
- **Validación de cliente** para membresías
- **Validación de tiempo** para reversiones (24h)
- **Validación de permisos** para operaciones sensibles

## 🛠️ Instalación y Configuración

### **1. Backend**
```bash
cd Backend/
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python create_sales_tables.py  # Crear tablas
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Frontend**
```bash
cd Frontend/
npm install
npm run dev  # http://localhost:3000
```

### **3. Verificación**
```bash
# Probar sistema de ventas
python test_sales_api.py
```

## 📱 Interfaces de Usuario

### **1. Dashboard de Ventas** (`/sales`)
- **Cards interactivas** para navegación
- **Acceso rápido** a POS e historial
- **Resumen de características** del sistema

### **2. Punto de Venta** (`/sales/pos`)
- **Layout dividido**: Productos | Carrito
- **Tabs**: Productos vs Membresías
- **Búsqueda en tiempo real**
- **Carrito con cálculos automáticos**
- **Dialog de pago con múltiples métodos**

### **3. Historial de Ventas** (`/sales/history`)
- **Tabla con filtros avanzados**
- **Paginación eficiente**
- **Detalles completos por venta**
- **Funcionalidad de reversión**
- **Estados visuales claros**

## 🔧 API Endpoints

### **Ventas**
```
POST   /api/sales/                    # Crear venta
GET    /api/sales/                    # Listar ventas
GET    /api/sales/{id}                # Detalles de venta
POST   /api/sales/{id}/reverse        # Reversar venta
```

### **Productos y Planes**
```
GET    /api/sales/products/available       # Productos para venta
GET    /api/sales/membership-plans/available # Planes disponibles
POST   /api/sales/validate-stock           # Validar stock
```

### **Reportes**
```
GET    /api/sales/summary/statistics  # Resumen de ventas
```

## 📈 Métricas y Reportes

### **Métricas Disponibles**
- **Total de ventas** por período
- **Ingresos totales** y netos
- **Ventas por método de pago**
- **Productos más vendidos**
- **Membresías más populares**
- **Reversiones por período**

### **Filtros Disponibles**
- **Por fecha** (desde/hasta)
- **Por vendedor**
- **Por estado** de venta
- **Por tipo** de venta
- **Por método** de pago

## 🚦 Estados del Sistema

### **Estados de Venta**
- `pending`: Venta en proceso
- `completed`: Venta completada exitosamente
- `cancelled`: Venta cancelada
- `refunded`: Venta reembolsada/reversada

### **Tipos de Venta**
- `product`: Solo productos
- `membership`: Solo membresías
- `mixed`: Productos + membresías

### **Métodos de Pago**
- `cash`: Efectivo
- `nequi`: Nequi
- `bancolombia`: Bancolombia
- `daviplata`: Daviplata
- `card`: Tarjeta
- `transfer`: Transferencia

## 🔄 Integración con Otros Módulos

### **Con Inventario**
- ✅ Actualización automática de stock
- ✅ Validación de disponibilidad
- ✅ Registro de movimientos
- ✅ Reabastecimiento en reversiones

### **Con Membresías**
- ✅ Creación automática de membresías
- ✅ Activación inmediata
- ✅ Cálculo de fechas
- ✅ Cancelación en reversiones

### **Con Usuarios**
- ✅ Gestión de clientes
- ✅ Registro de vendedores
- ✅ Control de permisos
- ✅ Auditoría de acciones

## 🎯 Próximas Mejoras

### **Funcionalidades Planeadas**
- [ ] **Impresión de recibos** térmica
- [ ] **Códigos QR** para ventas
- [ ] **Descuentos por volumen** automáticos
- [ ] **Integración con contabilidad**
- [ ] **Reportes avanzados** con gráficos
- [ ] **Notificaciones push** de ventas
- [ ] **Backup automático** de transacciones

### **Optimizaciones Técnicas**
- [ ] **Cache de productos** frecuentes
- [ ] **Paginación virtual** para listas grandes
- [ ] **Sincronización offline**
- [ ] **Compresión de imágenes** de productos
- [ ] **Índices de base de datos** optimizados

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema de ventas:
- **Documentación API**: `http://localhost:8000/docs`
- **Logs del sistema**: `Backend/logs/`
- **Pruebas**: `python test_sales_api.py`

---

## 🎉 ¡Sistema de Ventas Listo!

El sistema de ventas está completamente implementado y listo para usar en producción. Incluye todas las funcionalidades necesarias para un gimnasio moderno con integración completa entre inventario, membresías y control de acceso.









