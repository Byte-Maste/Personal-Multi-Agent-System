from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.family_member import FamilyMember
from app.models.transaction import Transaction
from app.services.auth_service import get_current_user
from app.schemas.family import FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse, FamilyAggregation

router = APIRouter()


@router.get("/", response_model=dict)
async def list_family(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.user_id == current_user.id)
        .order_by(FamilyMember.created_at)
    )
    members = result.scalars().all()

    user_monthly_income = float(current_user.monthly_income or 0)
    member_list = []
    total_income = user_monthly_income

    for m in members:
        income = float(m.monthly_income or 0)
        total_income += income
        member_list.append({
            "id": str(m.id),
            "name": m.name,
            "relation": m.relation,
            "monthly_income": income,
            "contribution_ratio": None,
        })

    for m in member_list:
        if total_income > 0:
            m["contribution_ratio"] = round((m["monthly_income"] / total_income) * 100, 1)

    own_contribution_ratio = round((user_monthly_income / total_income) * 100, 1) if total_income > 0 else 100

    return {
        "members": member_list,
        "user_income": user_monthly_income,
        "aggregation": {
            "total_income": round(total_income, 2),
            "member_count": len(members) + 1,
            "own_contribution_ratio": own_contribution_ratio,
        },
    }


@router.post("/members", response_model=FamilyMemberResponse, status_code=201)
async def add_family_member(
    body: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = FamilyMember(
        user_id=current_user.id,
        name=body.name,
        relation=body.relation,
        monthly_income=body.monthly_income,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    result = await db.execute(
        select(FamilyMember).where(FamilyMember.user_id == current_user.id)
    )
    all_members = result.scalars().all()
    total_income = float(current_user.monthly_income or 0) + sum(float(m.monthly_income or 0) for m in all_members)
    contribution_ratio = round((float(member.monthly_income or 0) / total_income) * 100, 1) if total_income > 0 else None

    return FamilyMemberResponse(
        id=member.id,
        name=member.name,
        relation=member.relation,
        monthly_income=float(member.monthly_income) if member.monthly_income else None,
        contribution_ratio=contribution_ratio,
    )


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: str,
    body: FamilyMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == member_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    if body.monthly_income is not None:
        member.monthly_income = body.monthly_income
    if body.relation is not None:
        member.relation = body.relation

    await db.commit()
    await db.refresh(member)

    return FamilyMemberResponse(
        id=member.id,
        name=member.name,
        relation=member.relation,
        monthly_income=float(member.monthly_income) if member.monthly_income else None,
        contribution_ratio=None,
    )


@router.delete("/members/{member_id}")
async def remove_family_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == member_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    await db.delete(member)
    await db.commit()
    return {"status": "ok", "message": "Family member removed"}


@router.get("/dashboard")
async def family_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.user_id == current_user.id)
    )
    members = result.scalars().all()

    user_monthly_income = float(current_user.monthly_income or 0)
    total_income = user_monthly_income
    per_member = [{
        "name": current_user.name or "You",
        "income": user_monthly_income,
        "relation": "self",
    }]

    for m in members:
        income = float(m.monthly_income or 0)
        total_income += income
        per_member.append({
            "name": m.name,
            "income": income,
            "relation": m.relation,
        })

    txn_result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
        )
    )
    txns = txn_result.scalars().all()
    total_expenses = sum(float(t.amount) for t in txns if t.type == "debit")
    monthly_expenses = round(total_expenses / max(len(txns), 1) * 30, 2) if txns else 0
    net_savings = round(total_income - monthly_expenses, 2)
    combined_savings_rate = round(max(0, net_savings / total_income * 100), 1) if total_income > 0 else 0

    for p in per_member:
        if total_income > 0:
            p["contribution_pct"] = round((p["income"] / total_income) * 100, 1)
        else:
            p["contribution_pct"] = 0
        share = round(monthly_expenses * (p["contribution_pct"] / 100), 2) if p["contribution_pct"] else 0
        p["allocated_expenses"] = share
        p["savings"] = round(p["income"] - share, 2)

    return {
        "members": per_member,
        "aggregation": {
            "total_income": round(total_income, 2),
            "total_expenses": monthly_expenses,
            "net_savings": net_savings,
            "combined_savings_rate": combined_savings_rate,
        },
    }
