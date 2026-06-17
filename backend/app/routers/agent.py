from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.agents.graph import run_ingestion_pipeline
from app.services.auth_service import get_current_user

router = APIRouter()


@router.post("/run")
async def trigger_agent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await run_ingestion_pipeline(
        user_id=str(current_user.id),
        db=db,
    )
    return {
        "status": "completed",
        "health_score": result.get("health_score", 0),
        "transactions_count": len(result.get("transactions", [])),
        "category_summaries": result.get("category_summaries", {}),
        "utilization_report": result.get("utilization_report", {}),
        "budget_alerts": result.get("budget_alerts", []),
        "anomalies": result.get("anomalies", []),
        "subscriptions": result.get("subscriptions", []),
        "insights": result.get("insights", []),
        "execution_log": result.get("execution_log", []),
    }
