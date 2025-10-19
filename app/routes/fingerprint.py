from fastapi import APIRouter
from app.controllers.fingerprint_controller import router as fingerprint_router

router = APIRouter()
router.include_router(fingerprint_router)









