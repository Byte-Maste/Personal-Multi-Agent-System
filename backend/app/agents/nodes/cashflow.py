from datetime import datetime, timedelta, date
from collections import defaultdict
from sqlalchemy import select, desc

from app.agents.state import SharedState


async def cashflow_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("cashflow_node: START")
    db = get_graph_db()

    from app.models.statement import Statement
    user_id = state["user_id"]
    txns = state.get("transactions", [])
    today = date.today()

    stmt_result = await db.execute(
        select(Statement).where(Statement.user_id == user_id)
        .order_by(desc(Statement.created_at)).limit(1)
    )
    latest_stmt = stmt_result.scalar_one_or_none()
    opening_balance = 0.0
    if latest_stmt and latest_stmt.meta_data:
        opening_balance = float(
            latest_stmt.meta_data.get("closing_balance",
            latest_stmt.meta_data.get("opening_balance", 0))
        )
    log.append(f"cashflow_node: opening_balance=₹{opening_balance:,.2f}")

    daily_net: dict[str, float] = defaultdict(float)
    income_total = 0.0
    expense_total = 0.0

    for tx in txns:
        amount = float(tx.get("amount", 0))
        txn_type = tx.get("type", "unknown")
        txn_date = tx.get("transaction_date")

        if txn_date:
            try:
                day_key = txn_date.strftime("%Y-%m-%d") if hasattr(txn_date, "strftime") else str(txn_date)[:10]
            except Exception:
                day_key = "unknown"
        else:
            day_key = "unknown"

        if txn_type == "credit":
            daily_net[day_key] += amount
            income_total += amount
        elif txn_type == "debit":
            daily_net[day_key] -= amount
            expense_total += amount

    days_with_data = [k for k in daily_net.keys() if k != "unknown"]
    sorted_days = sorted(days_with_data)

    avg_daily_expense = expense_total / max(len(sorted_days), 1)
    avg_daily_income = income_total / max(len(sorted_days), 1)
    net_daily = avg_daily_income - avg_daily_expense

    projection_days = 30
    forecast = []
    running_balance = opening_balance

    for d in sorted_days:
        running_balance += daily_net[d]

    for i in range(projection_days):
        day = today + timedelta(days=i)
        projected = net_daily
        running_balance += projected
        forecast.append({
            "date": day.isoformat(),
            "projected_balance": round(running_balance, 2),
            "projected_net": round(projected, 2),
        })

    cashflow_forecast = {
        "current_balance": round(opening_balance, 2),
        "projected_balance_30d": round(running_balance, 2),
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_expense": round(avg_daily_expense, 2),
        "net_daily": round(net_daily, 2),
        "income_total": round(income_total, 2),
        "expense_total": round(expense_total, 2),
        "forecast": forecast,
        "lowest_balance_date": min(forecast, key=lambda f: f["projected_balance"])["date"] if forecast else "",
        "lowest_balance": round(min(f["projected_balance"] for f in forecast), 2) if forecast else 0,
    }

    log.append(f"cashflow_node: income=₹{income_total:,.0f} expenses=₹{expense_total:,.0f}")
    log.append(f"cashflow_node: current_balance=₹{opening_balance:,.2f}")
    log.append(f"cashflow_node: projected 30d balance=₹{cashflow_forecast['projected_balance_30d']:,.0f}")
    log.append("cashflow_node: END")
    return {
        **state,
        "cashflow_forecast": cashflow_forecast,
        "execution_log": log,
    }
