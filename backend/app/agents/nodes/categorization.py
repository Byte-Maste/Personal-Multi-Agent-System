from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.state import SharedState
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.categorization_service import categorize_batch


async def categorization_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("categorization_node: START")
    db = get_graph_db()
    user_id = state["user_id"]
    raw_txns = state.get("extracted_transactions", [])
    if not raw_txns:
        result = await db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.category_id == None,
            ).limit(100)
        )
        raw_txns = []
        for tx in result.scalars().all():
            d = {k: v for k, v in tx.__dict__.items() if not k.startswith("_")}
            d["amount"] = float(d["amount"]) if "amount" in d else 0
            raw_txns.append(d)

    if raw_txns:
        categorized = await categorize_batch(raw_txns)
        log.append(f"categorization_node: categorized {len(categorized)} transactions")
    else:
        categorized = []
        log.append("categorization_node: no transactions to categorize")

    summaries: dict[str, float] = {}
    category_map: dict[str, str] = {}
    for tx in categorized:
        cat_name = tx.get("category_name", "Other")
        summaries[cat_name] = summaries.get(cat_name, 0) + float(tx.get("amount", 0))

        if tx.get("category_name") and not category_map.get(tx["category_name"]):
            result = await db.execute(
                select(Category).where(
                    Category.name == tx["category_name"],
                    Category.is_default == True,
                )
            )
            cat = result.scalar_one_or_none()
            if cat:
                category_map[tx["category_name"]] = str(cat.id)

    log.append("categorization_node: END")
    return {
        **state,
        "transactions": categorized,
        "category_id_map": {**state.get("category_id_map", {}), **category_map},
        "category_summaries": {**state.get("category_summaries", {}), **summaries},
        "execution_log": log,
    }
