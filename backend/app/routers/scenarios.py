from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.scenario import Scenario
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.auth_service import get_current_user
from app.schemas.scenario import ScenarioSimulate, ScenarioResponse

router = APIRouter()


async def _get_user_financials(user_id: str, db: AsyncSession) -> dict:
    txn_result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
        )
    )
    txns = txn_result.scalars().all()

    income_total = sum(float(t.amount) for t in txns if t.type == "credit")
    expense_total = sum(float(t.amount) for t in txns if t.type == "debit")
    monthly_income = income_total / max(len(txns), 1) * 30
    monthly_expenses = expense_total / max(len(txns), 1) * 30

    cat_result = await db.execute(
        select(Transaction, Category).join(Category, Transaction.category_id == Category.id, isouter=True).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
        )
    )
    rows = cat_result.all()

    category_expenses = {}
    for txn, cat in rows:
        if txn.type == "debit":
            cat_name = cat.name if cat else "Other"
            category_expenses[cat_name] = category_expenses.get(cat_name, 0) + float(txn.amount)

    return {
        "monthly_income": round(monthly_income, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "savings_rate": round(max(0, (monthly_income - monthly_expenses) / monthly_income * 100), 1) if monthly_income > 0 else 0,
        "category_expenses": category_expenses,
    }


@router.post("/simulate")
async def simulate_scenario(
    body: ScenarioSimulate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fin = await _get_user_financials(str(current_user.id), db)
    monthly_income = fin["monthly_income"]
    monthly_expenses = fin["monthly_expenses"]
    savings_rate = fin["savings_rate"]
    category_expenses = fin.get("category_expenses", {})
    user_income = float(current_user.monthly_income or monthly_income)

    projected_impact = {}
    recommendation = ""
    name = ""

    if body.scenario_type == "salary_hike":
        hike_pct = float(body.inputs.get("hike_percentage", 0))
        if hike_pct <= 0:
            raise HTTPException(status_code=422, detail="hike_percentage must be > 0")
        hike_month = body.inputs.get("hike_month", date.today().isoformat()[:7])

        new_income = user_income * (1 + hike_pct / 100)
        new_savings = new_income - monthly_expenses
        new_savings_rate = round(max(0, new_savings / new_income * 100), 1) if new_income > 0 else 0
        current_6m_balance = (user_income - monthly_expenses) * 6
        projected_6m_balance = new_savings * 6
        additional_yearly = (new_income - user_income) * 12

        projected_impact = {
            "new_monthly_income": round(new_income, 2),
            "new_savings_rate": new_savings_rate,
            "new_projected_balance_6m": round(projected_6m_balance, 2),
            "current_6m_balance": round(current_6m_balance, 2),
            "additional_yearly_savings": round(additional_yearly, 2),
        }
        recommendation = (
            f"With a {hike_pct:.0f}% hike (₹{user_income:,.0f} → ₹{new_income:,.0f}/mo), "
            f"your savings rate improves from {savings_rate:.0f}% to {new_savings_rate:.0f}%. "
            f"Increase SIP by ₹{additional_yearly/12:,.0f}/month to maximize long-term growth."
        )
        name = f"{hike_pct:.0f}% Salary Hike from {hike_month}"

    elif body.scenario_type == "job_loss":
        months_off = int(body.inputs.get("months_without_income", 6))
        severance = int(body.inputs.get("severance_months", 1))
        if months_off <= 0:
            raise HTTPException(status_code=422, detail="months_without_income must be > 0")

        current_balance = (user_income - monthly_expenses) * 3
        burn_rate = monthly_expenses
        months_before_depletion = round(current_balance / burn_rate, 1) if burn_rate > 0 else 0
        total_deficit = burn_rate * (months_off - severance)
        additional_fund_needed = max(0, total_deficit - current_balance)

        projected_impact = {
            "current_balance": round(current_balance, 2),
            "burn_rate": round(burn_rate, 2),
            "months_before_depletion": months_before_depletion,
            "total_deficit": round(total_deficit, 2),
            "additional_fund_needed": round(additional_fund_needed, 2),
            "severance_months": severance,
        }
        recommendation = (
            f"Without income for {months_off} months, you'd need ₹{total_deficit:,.0f}. "
            f"Current runway: {months_before_depletion} month(s). "
            f"Build emergency fund to ₹{burn_rate * 6:,.0f} (6 months of expenses)."
        )
        name = f"Job Loss — {months_off} months without income"

    elif body.scenario_type == "new_loan":
        loan_amount = float(body.inputs.get("loan_amount", 0))
        tenure_years = float(body.inputs.get("tenure_years", 5))
        interest_rate = float(body.inputs.get("interest_rate", 9.5))

        if loan_amount <= 0:
            raise HTTPException(status_code=422, detail="loan_amount must be > 0")
        if tenure_years <= 0:
            raise HTTPException(status_code=422, detail="tenure_years must be > 0")

        monthly_rate = (interest_rate / 100) / 12
        num_payments = tenure_years * 12
        if monthly_rate > 0:
            emi = loan_amount * monthly_rate * (1 + monthly_rate) ** num_payments / ((1 + monthly_rate) ** num_payments - 1)
        else:
            emi = loan_amount / num_payments

        emi_ratio = emi / user_income * 100
        new_expenses = monthly_expenses + emi
        new_savings = user_income - new_expenses
        new_savings_rate = round(max(0, new_savings / user_income * 100), 1) if user_income > 0 else 0

        max_affordable_emi = user_income * 0.25
        affordable_loan = 0
        if monthly_rate > 0:
            affordable_loan = max_affordable_emi * ((1 + monthly_rate) ** num_payments - 1) / (monthly_rate * (1 + monthly_rate) ** num_payments)

        projected_impact = {
            "emi": round(emi, 2),
            "emi_ratio": round(emi_ratio, 1),
            "new_savings_rate": new_savings_rate,
            "new_monthly_expenses": round(new_expenses, 2),
            "total_interest": round(emi * num_payments - loan_amount, 2),
            "affordable_loan_amount": round(affordable_loan, 2),
        }

        if emi_ratio > 25:
            recommendation = (
                f"EMI of ₹{emi:,.0f} is {emi_ratio:.0f}% of income — exceeds the 25% recommended limit. "
                f"Consider a loan of ₹{affordable_loan:,.0f} instead (EMI: ₹{max_affordable_emi:,.0f}/mo)."
            )
        else:
            recommendation = (
                f"EMI of ₹{emi:,.0f} is {emi_ratio:.0f}% of income — within safe limits. "
                f"Your new savings rate would be {new_savings_rate:.0f}%."
            )
        name = f"₹{loan_amount:,.0f} Loan at {interest_rate:.0f}% for {tenure_years:.0f}yr"

    else:
        raise HTTPException(status_code=422, detail=f"Unknown scenario_type: {body.scenario_type}")

    scenario = Scenario(
        user_id=current_user.id,
        name=name,
        scenario_type=body.scenario_type,
        inputs=body.inputs,
        projected_impact=projected_impact,
        recommendation=recommendation,
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    return {
        "scenario_id": str(scenario.id),
        "name": name,
        "current": {
            "monthly_income": round(user_income, 2),
            "monthly_expenses": round(monthly_expenses, 2),
            "savings_rate": savings_rate,
        },
        "projected": projected_impact,
        "recommendation": recommendation,
    }


@router.get("/")
async def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario).where(Scenario.user_id == current_user.id)
        .order_by(desc(Scenario.created_at))
        .limit(50)
    )
    scenarios = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "scenario_type": s.scenario_type,
            "inputs": s.inputs,
            "projected_impact": s.projected_impact,
            "recommendation": s.recommendation,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in scenarios
    ]
