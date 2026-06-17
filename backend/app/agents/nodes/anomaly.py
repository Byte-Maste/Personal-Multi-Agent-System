from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.agents.state import SharedState
from app.models.transaction import Transaction


async def anomaly_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("anomaly_node: START")
    db = get_graph_db()

    txns = state.get("transactions", [])
    anomalies = []

    merchant_amounts: dict[str, list[float]] = defaultdict(list)
    daily_totals: dict[str, float] = defaultdict(float)

    for tx in txns:
        merchant = tx.get("merchant", "") or ""
        amount = float(tx.get("amount", 0))
        if merchant:
            merchant_amounts[merchant].append(amount)

        txn_date = tx.get("transaction_date")
        if txn_date:
            try:
                day_key = txn_date.strftime("%Y-%m-%d") if hasattr(txn_date, "strftime") else str(txn_date)[:10]
            except Exception:
                day_key = "unknown"
            daily_totals[day_key] += amount

    for tx in txns:
        amount = float(tx.get("amount", 0))
        merchant = tx.get("merchant", "") or ""
        cat = tx.get("category_name") or ""
        reason = None

        if merchant and merchant in merchant_amounts and len(merchant_amounts[merchant]) >= 2:
            amounts = merchant_amounts[merchant]
            avg = sum(amounts) / len(amounts)
            if len(amounts) >= 3 and amount > avg * 3:
                reason = f"Amount ₹{amount:,.0f} is 3x above usual ₹{avg:,.0f} for {merchant}"
            elif len(amounts) >= 3 and amount < avg * 0.3:
                reason = f"Amount ₹{amount:,.0f} is unusually low for {merchant}"

        if not reason and amount > 50000 and cat != "Income":
            reason = f"Large debit ₹{amount:,.0f} not categorized as Income"
        if not reason and amount > 100000:
            reason = f"Very large amount ₹{amount:,.0f} — review required"

        if reason:
            anomalies.append({
                "transaction_id": str(tx.get("id", "")) if tx.get("id") else None,
                "description": tx.get("description", "")[:100],
                "amount": amount,
                "merchant": merchant,
                "reason": reason,
                "severity": "high" if amount > 50000 else "medium",
                "detected_at": datetime.utcnow().isoformat(),
            })

    user_id = state["user_id"]
    if not txns:
        result = await db.execute(
            select(Transaction).where(Transaction.user_id == user_id, Transaction.is_anomaly == True).limit(50)
        )
        db_anomalies = result.scalars().all()
        for atx in db_anomalies:
            anomalies.append({
                "transaction_id": str(atx.id),
                "description": atx.description or "",
                "amount": float(atx.amount),
                "merchant": atx.merchant or "",
                "reason": atx.anomaly_reason or "Flagged in bank data",
                "severity": "medium",
                "detected_at": str(atx.created_at) if atx.created_at else "",
            })

    log.append(f"anomaly_node: {len(anomalies)} anomalies detected")
    log.append("anomaly_node: END")
    return {
        **state,
        "anomalies": anomalies,
        "execution_log": log,
    }
