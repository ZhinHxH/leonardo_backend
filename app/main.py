from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, users, memberships, products, sales, reports, access_control, fingerprint, inventory, membership_plans, clinical_history
from app.core.config import settings
from app.core.logging_config import main_logger, exception_handler, log_function_call

logger = main_logger

app = FastAPI(
    title="Gym Management System API",
    description="API para el sistema de gestión de gimnasio",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de rutas
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/api/users", tags=["Usuarios"])
app.include_router(memberships.router, prefix="/api/memberships", tags=["Membresías"])
app.include_router(products.router, prefix="/api/products", tags=["Productos"])
app.include_router(sales.router, prefix="/api/sales", tags=["Ventas"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reportes"])
app.include_router(access_control.router, prefix="/api/access", tags=["Control de Acceso"])
app.include_router(fingerprint.router, prefix="/api", tags=["Huellas Dactilares"])
app.include_router(inventory.router, prefix="/api", tags=["Inventario"])
app.include_router(membership_plans.router, prefix="/api/membership-plans", tags=["Planes de Membresía"])
app.include_router(clinical_history.router, prefix="/api/clinical-history", tags=["Historia Clínica"])

@app.get("/")
@log_function_call(logger)
async def root():
    logger.info("🌐 Endpoint raíz accedido")
    return {"message": "Bienvenido al Sistema de Gestión de Gimnasio"}

@app.on_event("startup")
@exception_handler(logger, {"event": "startup"})
async def startup_event():
    logger.info("🚀 Aplicación iniciada - Sistema de Gestión de Gimnasio")
    logger.info(f"📊 Configuración CORS: {settings.CORS_ORIGINS}")
    logger.info(f"🗄️ URL de Base de Datos: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Configurada'}")

@app.on_event("shutdown")
@exception_handler(logger, {"event": "shutdown"})
async def shutdown_event():
    logger.info("🛑 Aplicación cerrada") 