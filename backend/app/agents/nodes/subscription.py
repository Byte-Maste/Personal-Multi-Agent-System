from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import SharedState


async def subscription_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("subscription_node: START")
    db = get_graph_db()

    txns = state.get("transactions", [])
    subscriptions = []

    merchant_months: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for tx in txns:
        merchant = (tx.get("merchant", "") or "").strip().lower()
        if not merchant:
            desc = (tx.get("description", "") or "").lower()
            name_words = desc.split()[:3]
            merchant = " ".join(name_words) if name_words else ""
        amount = float(tx.get("amount", 0))
        txn_type = tx.get("type", "unknown")
        if txn_type == "debit" or txn_type == "unknown":
            txn_date = tx.get("transaction_date")
            try:
                month_key = txn_date.strftime("%Y-%m") if hasattr(txn_date, "strftime") else str(txn_date)[:7]
            except Exception:
                month_key = "unknown"
            merchant_months[merchant][month_key].append(amount)

    subscription_keywords = ["netflix", "spotify", "prime", "youtube", "apple", "google", "chatgpt",
                             "github", "notion", "canva", "slack", "dropbox", "medium", "patreon",
                             "hotstar", "jiocinema", "sonyliv", "zee5", "disney"]

    for merchant, month_data in merchant_months.items():
        months_with_txns = [m for m, amts in month_data.items() if sum(amts) > 0]
        if len(months_with_txns) >= 2:
            avg_amounts = [sum(amts) / len(amts) for amts in month_data.values() if amts]
            if avg_amounts:
                overall_avg = sum(avg_amounts) / len(avg_amounts)
                max_deviation = max(abs(a - overall_avg) for a in avg_amounts) if avg_amounts else 0
                is_fixed = max_deviation < overall_avg * 0.3 if overall_avg > 0 else False
                is_keyword = any(kw in merchant for kw in subscription_keywords)

                if (is_fixed and overall_avg < 20000) or is_keyword:
                    subscriptions.append({
                        "merchant": merchant,
                        "estimated_amount": round(overall_avg, 2),
                        "frequency": "monthly",
                        "confidence": "high" if is_keyword else "medium",
                        "months_detected": len(months_with_txns),
                    })

    total_subscription_cost = sum(s["estimated_amount"] for s in subscriptions)

    log.append(f"subscription_node: {len(subscriptions)} subscriptions found, total ₹{total_subscription_cost:,.0f}/mo")
    log.append("subscription_node: END")
    return {
        **state,
        "subscriptions": subscriptions,
        "execution_log": log,
    }
