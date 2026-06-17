from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.agents.state import SharedState
from app.models.alert import Alert


async def notification_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("notification_node: START")
    db = get_graph_db()

    user_id = state["user_id"]
    alerts_to_create = list(state.get("alerts_to_create", []))

    budget_alerts = state.get("budget_alerts", [])
    anomalies = state.get("anomalies", [])
    health_score = state.get("health_score", 0)
    cashflow = state.get("cashflow_forecast", {})

    existing = await db.execute(
        select(Alert).where(Alert.user_id == user_id, Alert.is_read == False)
    )
    existing_alerts = {a.alert_type for a in existing.scalars().all()}

    new_alert_count = 0
    for ba in budget_alerts:
        alert_type = f"budget_{ba.get('category', 'unknown')}"
        if alert_type in existing_alerts:
            continue
        alerts_to_create.append({
            "type": alert_type,
            "severity": ba.get("severity", "info"),
            "title": f"Budget Alert: {ba.get('category', '')}",
            "message": ba.get("message", ""),
            "meta": ba,
        })
        new_alert_count += 1

    for ax in anomalies:
        alert_type = f"anomaly_{ax.get('transaction_id', 'unknown')}"
        if alert_type in existing_alerts:
            continue
        alerts_to_create.append({
            "type": alert_type,
            "severity": ax.get("severity", "medium"),
            "title": "Anomaly Detected",
            "message": ax.get("reason", "")[:500],
            "meta": ax,
        })
        new_alert_count += 1

    if health_score < 40 and "health_score_low" not in existing_alerts:
        alerts_to_create.append({
            "type": "health_score_low",
            "severity": "warning",
            "title": "Financial Health Score Low",
            "message": f"Your financial health score is {health_score}/100. Review budget recommendations.",
            "meta": {"health_score": health_score},
        })
        new_alert_count += 1

    low_balance = cashflow.get("lowest_balance", 0)
    if low_balance < 0 and "cashflow_negative" not in existing_alerts:
        alerts_to_create.append({
            "type": "cashflow_negative",
            "severity": "critical",
            "title": "Cash Flow Warning",
            "message": f"Projected balance may go negative (₹{low_balance:,.0f}) within 30 days.",
            "meta": {"lowest_balance": low_balance, "date": cashflow.get("lowest_balance_date", "")},
        })
        new_alert_count += 1

    for alert_data in alerts_to_create:
        if "id" not in alert_data:
            db_alert = Alert(
                user_id=user_id,
                alert_type=alert_data["type"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                message=alert_data["message"],
                meta_data=alert_data.get("meta", None),
            )
            db.add(db_alert)

    if alerts_to_create:
        await db.commit()

    log.append(f"notification_node: {new_alert_count} new alerts created")
    log.append("notification_node: END")
    return {
        **state,
        "alerts_to_create": alerts_to_create,
        "execution_log": log,
    }
