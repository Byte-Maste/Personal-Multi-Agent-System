from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def insights_root():
    return {"message": "Insights routes stub"}
