from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.agents.state import SharedState
from app.models.transaction import Transaction
from app.models.budget import Budget


async def health_score_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("health_score_node: START")
    db = get_graph_db()

    user_id = state["user_id"]
    txns = state.get("transactions", [])
    utilization = state.get("utilization_report", {})

    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            Transaction.is_anomaly == True,
        )
    )
    anomaly_count = result.scalar() or 0

    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            Transaction.is_recurring == True,
        )
    )
    recurring_count = result.scalar() or 0

    total_txns = len(txns)
    savings_pct = utilization.get("savings_pct", 0)
    needs_pct = utilization.get("needs_pct", 50)
    wants_pct = utilization.get("wants_pct", 30)

    savings_score = min(100, (savings_pct / 20) * 100) if savings_pct > 0 else 0
    needs_score = max(0, 100 - max(0, needs_pct - 50) * 5)
    wants_score = max(0, 100 - max(0, wants_pct - 30) * 5)
    anomaly_penalty = min(30, anomaly_count * 10)
    recurring_bonus = min(10, recurring_count * 2) if total_txns > 0 else 0
    stability_score = min(100, recurring_bonus * 10) if recurring_count > 3 else 30

    health_score = max(0, min(100, int(
        savings_score * 0.30 +
        needs_score * 0.25 +
        wants_score * 0.15 +
        (100 - anomaly_penalty) * 0.20 +
        stability_score * 0.10
    )))

    health_breakdown = {
        "savings_consistency": round(savings_score, 1),
        "needs_ratio": round(needs_score, 1),
        "wants_control": round(wants_score, 1),
        "anomaly_risk": round(max(0, 100 - anomaly_penalty), 1),
        "stability": round(stability_score, 1),
    }

    log.append(f"health_score_node: score={health_score}/100")
    log.append("health_score_node: END")
    return {
        **state,
        "health_score": health_score,
        "health_breakdown": health_breakdown,
        "execution_log": log,
    }
