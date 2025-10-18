from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_access_control():
    return {"message": "Access control endpoint"}
