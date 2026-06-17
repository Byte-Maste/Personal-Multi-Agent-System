from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def alerts_root():
    return {"message": "Alerts routes stub"}
