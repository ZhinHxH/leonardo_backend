from fastapi import APIRouter
from app.controllers.membership_plans_controller import router as membership_plans_router

router = APIRouter()
router.include_router(membership_plans_router)









