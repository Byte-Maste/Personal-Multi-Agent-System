from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import SharedState


async def budget_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("budget_node: START")
    db = get_graph_db()

    txns = state.get("transactions", [])
    cat_summaries = state.get("category_summaries", {})

    total_income = 0.0
    total_needs = 0.0
    total_wants = 0.0
    total_savings = 0.0

    needs_cats = {"Bills & EMI", "Bills & Utilities", "Rent", "Healthcare", "Insurance", "Transportation", "Education"}
    wants_cats = {"Food & Dining", "Shopping", "Entertainment", "Subscriptions", "Cash Withdrawal"}
    savings_cats = {"Investments", "Income", "Refund"}

    for tx in txns:
        amount = float(tx.get("amount", 0))
        txn_type = tx.get("type", "unknown")
        cat = tx.get("category_name") or "Other"
        if txn_type == "credit" and cat == "Income":
            total_income += amount
        elif txn_type == "debit" or txn_type == "unknown":
            if cat in needs_cats:
                total_needs += amount
            elif cat in wants_cats:
                total_wants += amount
            elif cat in savings_cats:
                total_savings += amount
            elif amount > 0:
                total_wants += amount

    income = total_income or 100000
    needs_pct = (total_needs / income) * 100
    wants_pct = (total_wants / income) * 100
    savings_pct = (total_savings / income) * 100

    utilization_report = {
        "total_income": round(total_income, 2),
        "total_needs": round(total_needs, 2),
        "total_wants": round(total_wants, 2),
        "total_savings": round(total_savings, 2),
        "needs_pct": round(needs_pct, 1),
        "wants_pct": round(wants_pct, 1),
        "savings_pct": round(savings_pct, 1),
        "needs_target_pct": 50,
        "wants_target_pct": 30,
        "savings_target_pct": 20,
    }

    budget_alerts = []
    if needs_pct > 55:
        budget_alerts.append({
            "type": "over_budget",
            "category": "Needs",
            "message": f"Needs at {needs_pct:.0f}% of income (target: 50%) — reduce discretionary spending",
            "severity": "warning",
        })
    if savings_pct < 15:
        budget_alerts.append({
            "type": "under_saving",
            "category": "Savings",
            "message": f"Savings at {savings_pct:.0f}% of income (target: 20%) — try to save more",
            "severity": "warning",
        })

    rebalance_recommendations = []
    if needs_pct > 50:
        excess = total_needs - (income * 0.50)
        rebalance_recommendations.append({
            "area": "Needs",
            "action": f"Reduce needs by ₹{excess:,.0f}/month to meet 50% target",
            "potential_saving": round(excess, 2),
        })
    if wants_pct > 30:
        excess = total_wants - (income * 0.30)
        rebalance_recommendations.append({
            "area": "Wants",
            "action": f"Reduce wants by ₹{excess:,.0f}/month to meet 30% target",
            "potential_saving": round(excess, 2),
        })
    if savings_pct < 20:
        gap = (income * 0.20) - total_savings
        rebalance_recommendations.append({
            "area": "Savings",
            "action": f"Increase savings by ₹{gap:,.0f}/month to meet 20% target",
            "potential_saving": round(gap, 2),
        })

    log.append(f"budget_node: needs={needs_pct:.0f}% wants={wants_pct:.0f}% savings={savings_pct:.0f}%")
    log.append(f"budget_node: {len(budget_alerts)} alerts, {len(rebalance_recommendations)} recommendations")
    log.append("budget_node: END")
    return {
        **state,
        "utilization_report": utilization_report,
        "budget_alerts": budget_alerts,
        "rebalance_recommendations": rebalance_recommendations,
        "execution_log": log,
    }
