from collections import defaultdict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.state import SharedState
from app.models.transaction import Transaction


async def spending_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("spending_node: START")
    db = get_graph_db()

    user_id = state["user_id"]
    txns = state.get("transactions", [])

    if not txns:
        result = await db.execute(
            select(Transaction).where(Transaction.user_id == user_id).limit(500)
        )
        txns = []
        for t in result.scalars().all():
            d = {k: v for k, v in t.__dict__.items() if not k.startswith("_")}
            d["amount"] = float(d["amount"]) if "amount" in d else 0
            txns.append(d)

    category_summaries: dict[str, float] = defaultdict(float)
    monthly_summaries: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    trends = []

    for tx in txns:
        cat_name = tx.get("category_name") or "Other"
        amount = float(tx.get("amount", 0))
        txn_type = tx.get("type", "unknown")
        if txn_type == "credit":
            category_summaries[cat_name] = category_summaries.get(cat_name, 0) + amount
        elif txn_type == "debit":
            category_summaries[cat_name] = category_summaries.get(cat_name, 0) - amount

        txn_date = tx.get("transaction_date")
        if txn_date:
            try:
                month_key = txn_date.strftime("%Y-%m") if hasattr(txn_date, "strftime") else str(txn_date)[:7]
            except Exception:
                month_key = "unknown"
            monthly_summaries[month_key][cat_name] = monthly_summaries[month_key].get(cat_name, 0) + amount

    sorted_months = sorted(monthly_summaries.keys())
    for month in sorted_months:
        cats = monthly_summaries[month]
        trends.append({
            "month": month,
            "total_spent": sum(v for v in cats.values() if v < 0) * -1 if any(v < 0 for v in cats.values()) else 0,
            "total_income": sum(v for v in cats.values() if v > 0),
            "top_category": max(cats, key=cats.get) if cats else "None",
        })

    log.append(f"spending_node: {len(category_summaries)} categories, {len(trends)} monthly trends")
    log.append("spending_node: END")
    return {
        **state,
        "transactions": txns,
        "category_summaries": dict(category_summaries),
        "monthly_summaries": {k: dict(v) for k, v in monthly_summaries.items()},
        "trends": trends,
        "execution_log": log,
    }
