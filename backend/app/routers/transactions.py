from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.auth_service import get_current_user
from app.schemas.transaction import TransactionResponse, TransactionListResponse

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category_id: str | None = None,
    txn_type: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted == False,
    )

    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if txn_type:
        query = query.where(Transaction.type == txn_type)
    if search:
        query = query.where(
            Transaction.merchant.ilike(f"%{search}%") |
            Transaction.description.ilike(f"%{search}%")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    txns = result.scalars().all()

    items = []
    for tx in txns:
        cat_name = None
        if tx.category_id:
            cat_result = await db.execute(select(Category).where(Category.id == tx.category_id))
            cat = cat_result.scalar_one_or_none()
            cat_name = cat.name if cat else None
        items.append(TransactionResponse(
            id=str(tx.id),
            transaction_date=tx.transaction_date,
            description=tx.description,
            merchant=tx.merchant,
            amount=float(tx.amount),
            currency=tx.currency,
            type=tx.type,
            category_id=str(tx.category_id) if tx.category_id else None,
            category_name=cat_name,
            subcategory=tx.subcategory,
            is_recurring=tx.is_recurring,
            is_anomaly=tx.is_anomaly,
        ))

    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{tx_id}/category")
async def update_transaction_category(
    tx_id: str,
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == tx_id,
            Transaction.user_id == current_user.id,
        )
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    cat_result = await db.execute(select(Category).where(Category.id == category_id))
    cat = cat_result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    tx.category_id = cat.id
    await db.commit()
    return {"status": "ok", "transaction_id": tx_id, "category_id": category_id}


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Category).where(
            (Category.user_id == current_user.id) | (Category.is_default == True)
        ).order_by(Category.name)
    )
    cats = result.scalars().all()
    return [
        {"id": str(c.id), "name": c.name, "type": c.type, "is_default": c.is_default}
        for c in cats
    ]
