# Backend del Sistema de Gestión de Gimnasio

## Descripción
Backend desarrollado con FastAPI para el sistema de gestión de gimnasio. Implementa una arquitectura MVC y utiliza MySQL como base de datos.

## Características
- Autenticación y autorización con JWT
- Control de acceso biométrico facial
- Gestión de membresías y planes
- Sistema de ventas y facturación
- Gestión de inventario
- Reportes y estadísticas
- API RESTful

## Requisitos
- Python 3.9+
- MySQL 8.0+
- OpenCV
- Face Recognition

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd Backend
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. Iniciar el servidor:
```bash
uvicorn app.main:app --reload
```

## Estructura del Proyecto
```
Backend/
├── app/
│   ├── controllers/     # Controladores de la aplicación
│   ├── models/         # Modelos de la base de datos
│   ├── services/       # Lógica de negocio
│   ├── routes/         # Rutas de la API
│   ├── utils/          # Utilidades
│   └── core/           # Configuración core
├── tests/              # Pruebas unitarias
└── requirements.txt    # Dependencias
```

## API Endpoints

### Autenticación
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout

### Usuarios
- GET /api/users
- POST /api/users
- GET /api/users/{id}
- PUT /api/users/{id}
- DELETE /api/users/{id}

### Membresías
- GET /api/memberships
- POST /api/memberships
- GET /api/memberships/{id}
- PUT /api/memberships/{id}
- DELETE /api/memberships/{id}

### Productos
- GET /api/products
- POST /api/products
- GET /api/products/{id}
- PUT /api/products/{id}
- DELETE /api/products/{id}

### Ventas
- GET /api/sales
- POST /api/sales
- GET /api/sales/{id}
- GET /api/sales/reports

### Control de Acceso
- POST /api/access/verify
- POST /api/access/register-face
- GET /api/access/history

## Documentación
La documentación de la API está disponible en:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Pruebas
```bash
pytest
```

## Contribución
1. Fork el repositorio
2. Crear una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Crear un Pull Request

## Licencia
Este proyecto está bajo la Licencia MIT. 