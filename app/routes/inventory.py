from fastapi import APIRouter
from app.controllers.inventory_controller import router as inventory_router

router = APIRouter()
router.include_router(inventory_router)









