from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.auth_service import get_current_user
from app.agents.graph import run_ingestion_pipeline

router = APIRouter()


@router.get("/")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await run_ingestion_pipeline(
        user_id=str(current_user.id),
        db=db,
    )

    cashflow = result.get("cashflow_forecast", {})
    utilization = result.get("utilization_report", {})

    monthly_expenses = float(utilization.get("total_needs", 0) + utilization.get("total_wants", 0))
    current_balance = float(cashflow.get("current_balance", 0))
    emergency_months = round(current_balance / monthly_expenses, 1) if monthly_expenses > 0 else 0

    ef_score = min(100, (emergency_months / 6) * 100)

    txn_result = await db.execute(
        select(Transaction, Category).join(
            Category, Transaction.category_id == Category.id, isouter=True
        ).where(
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
            Transaction.type == "debit",
        )
    )
    rows = txn_result.all()
    category_debits = {}
    for txn, cat in rows:
        cat_name = cat.name if cat else "Other"
        category_debits[cat_name] = category_debits.get(cat_name, 0) + float(txn.amount)

    bills_emi = category_debits.get("Bills & EMI", 0)
    monthly_income = float(current_user.monthly_income or utilization.get("total_income", monthly_expenses * 2))
    debt_ratio = round((bills_emi / max(monthly_income, 1)) * 100, 1) if monthly_income > 0 else 0
    debt_score = max(0, 100 - (debt_ratio / 25) * 100)

    savings_pct = float(utilization.get("savings_pct", 0))
    savings_score = min(100, (savings_pct / 20) * 100)

    risk_map = {"conservative": 60, "moderate": 75, "aggressive": 90}
    risk_prof = current_user.risk_profile or "moderate"
    risk_score = risk_map.get(risk_prof, 75)

    score = int(ef_score * 0.30 + debt_score * 0.25 + savings_score * 0.25 + risk_score * 0.20)

    if risk_prof == "conservative":
        allocation = {"equity": "20%", "debt": "60%", "gold": "10%", "cash": "10%"}
    elif risk_prof == "aggressive":
        allocation = {"equity": "65%", "debt": "20%", "gold": "10%", "cash": "5%"}
    else:
        allocation = {"equity": "40%", "debt": "40%", "gold": "10%", "cash": "10%"}

    if emergency_months < 3:
        rec = "Build 6-month emergency fund before starting aggressive investments"
    elif debt_ratio > 25:
        rec = "Reduce debt (EMI at {:.0f}% of income) before increasing investments".format(debt_ratio)
    elif savings_pct < 15:
        rec = "Increase savings rate to 20%+ before diversifying investments"
    else:
        rec = "Good financial foundation — consider increasing equity allocation for long-term growth"

    investment_readiness = {
        "score": score,
        "breakdown": {
            "emergency_fund": round(ef_score, 1),
            "debt_ratio": round(debt_score, 1),
            "savings_consistency": round(savings_score, 1),
            "risk_alignment": round(risk_score, 1),
        },
        "emergency_fund_months": emergency_months,
        "debt_ratio_pct": debt_ratio,
        "recommendation": rec,
        "suggested_allocation": allocation,
    }

    return {
        "category_summaries": result.get("category_summaries", {}),
        "monthly_summaries": result.get("monthly_summaries", {}),
        "trends": result.get("trends", []),
        "utilization_report": result.get("utilization_report", {}),
        "budget_alerts": result.get("budget_alerts", []),
        "rebalance_recommendations": result.get("rebalance_recommendations", []),
        "health_score": result.get("health_score", 0),
        "health_breakdown": result.get("health_breakdown", {}),
        "anomalies": result.get("anomalies", []),
        "subscriptions": result.get("subscriptions", []),
        "cashflow_forecast": result.get("cashflow_forecast", {}),
        "insights": result.get("insights", []),
        "investment_readiness": investment_readiness,
        "execution_log": result.get("execution_log", []),
    }
