# 🏥 Sistema de Historial Clínico - Gimnasio

## 📋 Descripción General

El Sistema de Historial Clínico permite llevar un registro detallado del progreso físico y nutricional de los miembros del gimnasio, similar a una historia clínica médica pero enfocada en fitness y bienestar.

## 🗄️ Modelos de Datos

### 1. ClinicalHistory
Registro principal del historial clínico de cada usuario.

```python
class ClinicalHistory(Base):
    id: int                    # ID único del registro
    user_id: int              # ID del usuario (FK)
    created_by: int           # ID de quien creó el registro (FK)
    history_type: HistoryType # Tipo de registro
    
    # Datos físicos
    weight: float             # Peso en kg
    height: float             # Altura en cm
    body_fat_percentage: float # Porcentaje de grasa corporal
    muscle_mass: float        # Masa muscular
    bmi: float               # Índice de masa corporal
    
    # Medidas corporales
    chest: float             # Pecho en cm
    waist: float             # Cintura en cm
    hips: float              # Caderas en cm
    arms: float              # Brazos en cm
    thighs: float            # Muslos en cm
    
    # Notas y observaciones
    notes: str               # Notas principales
    recommendations: str     # Recomendaciones
    
    # Objetivos
    goal_description: str    # Descripción del objetivo
    target_weight: float     # Peso objetivo
    target_date: datetime    # Fecha objetivo
    
    # Archivos
    attachment_url: str      # URL de archivos adjuntos
    attachment_type: str     # Tipo de archivo
    
    # Metadatos
    is_private: bool         # Solo visible para médicos/nutricionistas
    created_at: datetime     # Fecha de creación
    updated_at: datetime     # Fecha de actualización
```

### 2. UserGoal
Objetivos y metas específicas de cada usuario.

```python
class UserGoal(Base):
    id: int                  # ID único
    user_id: int            # ID del usuario (FK)
    created_by: int         # ID de quien creó el objetivo (FK)
    
    # Información del objetivo
    title: str              # Título del objetivo
    description: str        # Descripción detallada
    category: str           # Categoría (weight_loss, muscle_gain, etc.)
    
    # Valores
    current_value: float    # Valor actual
    target_value: float     # Valor objetivo
    unit: str              # Unidad de medida
    
    # Fechas
    start_date: datetime    # Fecha de inicio
    target_date: datetime   # Fecha objetivo
    completed_date: datetime # Fecha de completado
    
    # Estado
    is_active: bool         # Objetivo activo
    is_completed: bool      # Objetivo completado
    progress_percentage: float # Porcentaje de progreso
```

### 3. MembershipPlan
Planes de membresía y tarifas del gimnasio.

```python
class MembershipPlan(Base):
    id: int                    # ID único
    name: str                  # Nombre del plan
    description: str           # Descripción
    plan_type: str            # Tipo (monthly, daily, weekly, yearly)
    
    # Precios
    price: float              # Precio normal
    discount_price: float     # Precio con descuento
    
    # Configuración
    duration_days: int        # Duración en días
    access_hours_start: str   # Hora de inicio de acceso
    access_hours_end: str     # Hora de fin de acceso
    
    # Servicios incluidos
    includes_trainer: bool    # Incluye entrenador personal
    includes_nutritionist: bool # Incluye nutricionista
    includes_pool: bool       # Incluye piscina
    includes_classes: bool    # Incluye clases grupales
    max_guests: int          # Máximo de invitados
    
    # Límites
    max_visits_per_day: int   # Máximo de visitas por día
    max_visits_per_month: int # Máximo de visitas por mes
    
    # Estado
    is_active: bool           # Plan activo
    is_popular: bool          # Plan destacado
    sort_order: int          # Orden de visualización
```

## 🎯 Tipos de Registro (HistoryType)

- **WEIGHT_UPDATE**: Actualización de peso
- **MEASUREMENT**: Medidas corporales
- **NUTRITIONIST_NOTE**: Notas del nutricionista
- **TRAINER_NOTE**: Notas del entrenador
- **MEDICAL_NOTE**: Notas médicas
- **GOAL_UPDATE**: Actualización de objetivos
- **PROGRESS_PHOTO**: Fotos de progreso
- **WORKOUT_PLAN**: Plan de entrenamiento
- **DIET_PLAN**: Plan dietético

## 🔧 Funcionalidades Implementadas

### Frontend
1. **Gestión de Usuarios Completa (CRUD)**
   - Lista de usuarios con filtros avanzados
   - Formulario de registro con validación
   - Edición de usuarios
   - Eliminación con confirmación
   - Vista detallada con tabs

2. **Historial Clínico Profesional**
   - Timeline visual del progreso
   - Filtros por tipo de registro
   - Gráficos de evolución
   - Formularios especializados por tipo
   - Sistema de permisos

3. **Gestión de Roles y Permisos**
   - CRUD completo de roles
   - Sistema de permisos granular
   - Validación de eliminación
   - Interfaz intuitiva

4. **Gestión de Planes de Membresía**
   - Creación de planes personalizados
   - Configuración de servicios incluidos
   - Precios y descuentos
   - Horarios de acceso

5. **Sistema de Temas**
   - Tema claro/oscuro
   - Paleta personalizada (Negro, Dorado, Blanco)
   - Persistencia en localStorage
   - Componentes adaptados

### Backend
1. **Modelos de Datos Robustos**
   - Relaciones bien definidas
   - Validaciones automáticas
   - Campos de auditoría
   - Enums para consistencia

2. **Sistema de Logging Avanzado**
   - Logs estructurados en JSON
   - Manejo de excepciones
   - Decoradores automáticos
   - Archivos rotativos

## 🎨 Paleta de Colores

### Tema Claro
- **Primario**: Negro (#000000)
- **Secundario**: Dorado (#FFD700)
- **Fondo**: Blanco (#FFFFFF)
- **Texto**: Negro (#000000)

### Tema Oscuro
- **Primario**: Dorado (#FFD700)
- **Secundario**: Blanco (#FFFFFF)
- **Fondo**: Gris Oscuro (#121212)
- **Texto**: Blanco (#FFFFFF)

## 🚀 Instalación y Configuración

### 1. Backend
```bash
cd Backend
python app/scripts/create_clinical_tables.py
```

### 2. Frontend
```bash
cd Frontend
npm install
npm run dev
```

## 📱 Páginas Implementadas

### Administración
- `/users` - Lista de usuarios
- `/users/register` - Registro de usuarios
- `/users/clinical-history` - Historial clínico
- `/admin/roles` - Gestión de roles
- `/admin/membership-plans` - Planes de membresía

### Operaciones
- `/inventory` - Gestión de inventario
- `/sales` - Historial de ventas
- `/dashboard` - Panel principal

## 🔒 Control de Acceso

### Roles y Permisos
- **Admin**: Acceso completo
- **Manager**: Gestión operativa
- **Trainer**: Entrenamiento y seguimiento
- **Receptionist**: Atención y ventas
- **Member**: Acceso básico

### Protección de Rutas
```typescript
<AdminRoute allowedRoles={['admin', 'manager']}>
  // Contenido solo para admins y managers
</AdminRoute>
```

## 📊 Características del Historial Clínico

### Timeline Visual
- Registros ordenados cronológicamente
- Iconos distintivos por tipo
- Información contextual
- Filtros avanzados

### Tipos de Registro
1. **Peso y Medidas**: Seguimiento físico
2. **Notas Nutricionales**: Recomendaciones dietéticas
3. **Notas de Entrenamiento**: Progreso en ejercicios
4. **Objetivos**: Metas y seguimiento
5. **Fotos de Progreso**: Evidencia visual

### Funcionalidades Avanzadas
- Cálculo automático de IMC
- Gráficos de progreso
- Exportación de datos
- Sistema de notificaciones
- Recordatorios automáticos

## 🔧 Próximos Desarrollos

1. **Integración con ZKTeco**: Control de acceso biométrico
2. **Notificaciones Push**: Recordatorios y alertas
3. **App Móvil**: Aplicación nativa
4. **Reportes Avanzados**: Analytics y métricas
5. **Integración de Pagos**: Pasarelas de pago automáticas

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema, contactar al equipo de desarrollo.

---
*Sistema desarrollado con FastAPI, React, Next.js y Material-UI*








