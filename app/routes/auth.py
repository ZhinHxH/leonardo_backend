from fastapi import APIRouter
from app.controllers.auth_controller import router as auth_router

# Usar el router del controlador
router = auth_router
