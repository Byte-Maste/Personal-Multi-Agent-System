from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.auth_service import get_current_user
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse

router = APIRouter()


@router.get("/", response_model=dict)
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.created_at.desc())
    )
    goals = result.scalars().all()

    txn_result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
        )
    )
    txns = txn_result.scalars().all()
    monthly_expenses = sum(float(t.amount) for t in txns if t.type == "debit") / max(len(txns), 1) * 30
    monthly_income = float(current_user.monthly_income or 0)
    available_monthly = max(0, monthly_income - monthly_expenses)

    goal_responses = []
    total_monthly_required = 0.0
    for g in goals:
        target = float(g.target_amount)
        current_amt = float(g.current_amount or 0)
        progress_pct = round((current_amt / target) * 100, 1) if target > 0 else 0
        months_remaining = None
        feasible = True
        monthly_req = float(g.monthly_required or 0)

        if g.deadline and g.status == "active":
            today = date.today()
            remaining = (g.deadline - today).days
            months_remaining = max(1, remaining // 30)
            if monthly_req == 0 and target > current_amt:
                monthly_req = round((target - current_amt) / months_remaining, 2)
            available_for_goal = available_monthly - (total_monthly_required - monthly_req)
            feasible = monthly_req <= available_for_goal * 1.5

        total_monthly_required += monthly_req

        goal_responses.append({
            "id": str(g.id),
            "title": g.title,
            "target_amount": target,
            "current_amount": current_amt,
            "deadline": g.deadline.isoformat() if g.deadline else None,
            "monthly_required": monthly_req,
            "priority": g.priority,
            "status": g.status,
            "progress_pct": progress_pct,
            "months_remaining": months_remaining,
            "feasible": feasible,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {
        "goals": goal_responses,
        "total_monthly_required": round(total_monthly_required, 2),
        "available_monthly": round(available_monthly, 2),
        "shortfall": round(max(0, total_monthly_required - available_monthly), 2),
    }


@router.post("/", response_model=GoalResponse, status_code=201)
async def create_goal(
    body: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.target_amount <= 0:
        raise HTTPException(status_code=422, detail="target_amount must be > 0")

    monthly_required = None
    if body.deadline:
        today = date.today()
        remaining_days = (body.deadline - today).days
        if remaining_days <= 0:
            raise HTTPException(status_code=422, detail="deadline must be in the future")
        months_remaining = max(1, remaining_days // 30)
        monthly_required = round(body.target_amount / months_remaining, 2)

    goal = Goal(
        user_id=current_user.id,
        title=body.title,
        target_amount=body.target_amount,
        deadline=body.deadline,
        monthly_required=monthly_required,
        priority=body.priority,
        status="active",
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    target = float(goal.target_amount)
    current_amt = float(goal.current_amount or 0)
    progress_pct = round((current_amt / target) * 100, 1) if target > 0 else 0

    months_remaining = None
    if goal.deadline:
        remaining = (goal.deadline - date.today()).days
        months_remaining = max(1, remaining // 30)

    return GoalResponse(
        id=goal.id,
        title=goal.title,
        target_amount=target,
        current_amount=current_amt,
        deadline=goal.deadline,
        monthly_required=float(goal.monthly_required) if goal.monthly_required else None,
        priority=goal.priority,
        status=goal.status,
        progress_pct=progress_pct,
        months_remaining=months_remaining,
        feasible=True,
        created_at=goal.created_at.isoformat() if goal.created_at else "",
    )


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    body: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if body.current_amount is not None:
        if body.current_amount < 0:
            raise HTTPException(status_code=422, detail="current_amount cannot be negative")
        goal.current_amount = body.current_amount
    if body.status is not None:
        valid_statuses = ("active", "completed", "cancelled")
        if body.status not in valid_statuses:
            raise HTTPException(status_code=422, detail=f"status must be one of {valid_statuses}")
        goal.status = body.status

    await db.commit()
    await db.refresh(goal)

    target = float(goal.target_amount)
    current_amt = float(goal.current_amount or 0)
    progress_pct = round((current_amt / target) * 100, 1) if target > 0 else 0

    months_remaining = None
    if goal.deadline:
        remaining = (goal.deadline - date.today()).days
        months_remaining = max(1, remaining // 30)

    return GoalResponse(
        id=goal.id,
        title=goal.title,
        target_amount=target,
        current_amount=current_amt,
        deadline=goal.deadline,
        monthly_required=float(goal.monthly_required) if goal.monthly_required else None,
        priority=goal.priority,
        status=goal.status,
        progress_pct=progress_pct,
        months_remaining=months_remaining,
        feasible=True,
        created_at=goal.created_at.isoformat() if goal.created_at else "",
    )


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.status = "cancelled"
    await db.commit()
    return {"status": "ok", "message": "Goal cancelled"}


@router.get("/projection")
async def goal_projection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id, Goal.status == "active")
    )
    goals = result.scalars().all()

    projection = []
    total_monthly = 0.0
    for g in goals:
        target = float(g.target_amount)
        current_amt = float(g.current_amount or 0)
        monthly_req = float(g.monthly_required or 0)
        total_monthly += monthly_req

        months_to_goal = None
        if monthly_req > 0:
            months_to_goal = round((target - current_amt) / monthly_req)

        projection.append({
            "title": g.title,
            "target_amount": target,
            "current_amount": current_amt,
            "monthly_required": monthly_req,
            "months_to_goal": months_to_goal,
        })

    return {
        "projection": projection,
        "total_monthly_required": round(total_monthly, 2),
    }
