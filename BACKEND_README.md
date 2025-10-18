# Backend - Sistema de Gestión de Gimnasio

Este documento describe la arquitectura del backend siguiendo los principios SOLID y las mejores prácticas de desarrollo.

## 🏗️ Arquitectura SOLID

### 1. **Single Responsibility Principle (SRP)**
Cada clase tiene una única responsabilidad:
- `AuthService`: Manejo de autenticación y tokens
- `UserService`: Gestión de usuarios
- `AuthController`: Endpoints de autenticación
- `UserController`: Endpoints de usuarios

### 2. **Open/Closed Principle (OCP)**
El sistema está abierto para extensión pero cerrado para modificación:
- Nuevos roles se pueden agregar sin modificar código existente
- Nuevos servicios se pueden agregar siguiendo la interfaz base

### 3. **Liskov Substitution Principle (LSP)**
Las dependencias se pueden sustituir por implementaciones compatibles:
- Servicios inyectados a través de dependencias
- Interfaces bien definidas

### 4. **Interface Segregation Principle (ISP)**
Interfaces específicas para cada necesidad:
- Schemas específicos para cada operación
- Dependencias granulares

### 5. **Dependency Inversion Principle (DIP)**
Dependencias de alto nivel no dependen de detalles de bajo nivel:
- Uso de inyección de dependencias
- Separación de lógica de negocio y acceso a datos

## 📁 Estructura del Proyecto

```
Backend/
├── app/
│   ├── controllers/          # Controladores (Lógica de presentación)
│   │   └── auth_controller.py
│   ├── core/                 # Configuración central
│   │   ├── config.py
│   │   └── database.py
│   ├── dependencies/         # Dependencias de FastAPI
│   │   └── auth.py
│   ├── models/              # Modelos de SQLAlchemy
│   │   └── user.py
│   ├── routes/              # Rutas de la API
│   │   └── auth.py
│   ├── schemas/             # Schemas de Pydantic
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/            # Lógica de negocio
│   │   ├── auth_service.py
│   │   └── user_service.py
│   ├── scripts/             # Scripts de utilidad
│   │   └── init_db.py
│   └── main.py              # Punto de entrada
├── requirements.txt
└── README.md
```

## 🔧 Configuración

### Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos
DATABASE_URL=mysql+pymysql://user:password@localhost/gym_db

# Seguridad
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python -m alembic upgrade head

# Inicializar datos
python app/scripts/init_db.py

# Ejecutar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔐 Autenticación

### Endpoints Disponibles

#### POST `/api/auth/login`
Autenticación de usuarios.

**Request:**
```json
{
  "email": "admin@gym.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@gym.com",
    "name": "Administrador del Sistema",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": null
  }
}
```

#### POST `/api/auth/logout`
Cerrar sesión.

#### GET `/api/auth/me`
Obtener información del usuario actual.

#### POST `/api/auth/refresh`
Refrescar token de acceso.

#### POST `/api/auth/change-password`
Cambiar contraseña del usuario actual.

## 👥 Roles de Usuario

### Roles Disponibles
- **ADMIN**: Acceso completo al sistema
- **MANAGER**: Gestión de personal y reportes
- **TRAINER**: Gestión de entrenamientos y miembros
- **RECEPTIONIST**: Gestión de recepción y membresías
- **MEMBER**: Acceso limitado a funcionalidades de miembro

### Dependencias de Autorización

```python
from app.dependencies.auth import (
    require_admin,
    require_manager,
    require_trainer,
    require_receptionist,
    require_member,
    require_admin_or_manager,
    require_staff
)

@router.get("/admin-only")
async def admin_endpoint(current_user: User = Depends(require_admin)):
    return {"message": "Solo para administradores"}

@router.get("/staff-only")
async def staff_endpoint(current_user: User = Depends(require_staff)):
    return {"message": "Solo para personal"}
```

## 🗄️ Base de Datos

### Modelo de Usuario
```python
class User(Base):
    __tablename__ = "users"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    
    # Campos de identificación
    dni = Column(String(20), unique=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    blood_type = Column(Enum(BloodType), nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    
    # Campos de contacto
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    
    # Campos de seguridad y estado
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Campos de auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
```

## 🔧 Servicios

### AuthService
Maneja toda la lógica de autenticación:
- Verificación de contraseñas
- Generación y validación de tokens JWT
- Autenticación de usuarios
- Refresh de tokens

### UserService
Maneja la lógica de negocio de usuarios:
- CRUD de usuarios
- Validaciones de negocio
- Gestión de estados de usuario
- Cambio de contraseñas

## 🛡️ Seguridad

### JWT Tokens
- Algoritmo: HS256
- Expiración configurable
- Payload incluye ID, email y rol del usuario

### Contraseñas
- Hash con bcrypt
- Salt automático
- Verificación segura

### CORS
- Configuración específica para frontend
- Credenciales habilitadas
- Headers permitidos

## 📊 Usuarios de Prueba

Después de ejecutar `init_db.py`, se crean los siguientes usuarios:

| Email | Contraseña | Rol |
|-------|------------|-----|
| admin@gym.com | admin123 | ADMIN |
| manager@gym.com | manager123 | MANAGER |
| trainer@gym.com | trainer123 | TRAINER |
| receptionist@gym.com | reception123 | RECEPTIONIST |
| member@gym.com | member123 | MEMBER |

## 🚀 Despliegue

### Desarrollo
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 Próximos Pasos

1. **Implementar refresh tokens**
2. **Agregar logging estructurado**
3. **Implementar rate limiting**
4. **Agregar validación de email**
5. **Implementar recuperación de contraseña**
6. **Agregar auditoría de acciones**
7. **Implementar caché con Redis**
8. **Agregar tests unitarios y de integración**

## 🔍 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app

# Tests específicos
pytest tests/test_auth.py
```

## 📚 Documentación de la API

La documentación automática está disponible en:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`





