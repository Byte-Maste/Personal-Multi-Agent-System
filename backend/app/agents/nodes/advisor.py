import hashlib
import json
from collections import defaultdict

from sqlalchemy import select, func as sa_func

from app.agents.state import SharedState
from app.services.llm_client import llm_invoke


INSIGHT_SYSTEM_PROMPT = """You are a financial advisor AI. Given a user's financial data summary, generate:
1. Top 3 actionable insights (what they should do)
2. Top 3 positive observations (what they're doing well)
3. One specific recommendation for next month

Be concise, specific with amounts, and helpful. Use Indian currency format (₹)."""


async def advisor_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("advisor_node: START")
    db = get_graph_db()

    user_id = state["user_id"]
    utilization = state.get("utilization_report", {})
    health_score = state.get("health_score", 0)
    health_breakdown = state.get("health_breakdown", {})
    anomalies = state.get("anomalies", [])
    subscriptions = state.get("subscriptions", [])
    cashflow = state.get("cashflow_forecast", {})
    trends = state.get("trends", [])
    txns = state.get("transactions", [])

    from app.models.user import User
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    monthly_income = float(user.monthly_income) if user and user.monthly_income else None

    insights = []

    if monthly_income is None:
        income_txns = [
            tx for tx in txns
            if tx.get("type") == "credit" and tx.get("category_name") == "Income"
        ]
        merchant_amounts: dict[str, list[float]] = defaultdict(list)
        for tx in income_txns:
            merchant = tx.get("merchant") or tx.get("description", "")
            merchant_amounts[merchant].append(float(tx.get("amount", 0)))

        detected_salary = None
        detected_merchant = ""
        for merchant, amounts in merchant_amounts.items():
            if len(amounts) >= 1:
                avg_amount = sum(amounts) / len(amounts)
                if avg_amount > detected_salary if detected_salary else False:
                    pass
                if detected_salary is None or avg_amount > detected_salary:
                    detected_salary = avg_amount
                    detected_merchant = merchant

        if detected_salary and detected_salary > 10000:
            insights.append({
                "type": "actionable",
                "text": f"We detected ₹{detected_salary:,.0f}/mo from '{detected_merchant}' — is this your monthly income? Set it in Profile to enable budget tracking.",
            })
            log.append(f"advisor_node: auto-detected salary ₹{detected_salary:,.0f} from {detected_merchant}")

    budget_summary = (
        f"Income: ₹{utilization.get('total_income', 0):,.0f}, "
        f"Needs: ₹{utilization.get('total_needs', 0):,.0f} ({utilization.get('needs_pct', 0):.0f}%), "
        f"Wants: ₹{utilization.get('total_wants', 0):,.0f} ({utilization.get('wants_pct', 0):.0f}%), "
        f"Savings: ₹{utilization.get('total_savings', 0):,.0f} ({utilization.get('savings_pct', 0):.0f}%)"
    )
    anomaly_summary = f"{len(anomalies)} anomalies detected" if anomalies else "No unusual activity"
    sub_summary = f"{len(subscriptions)} subscriptions (₹{sum(s.get('estimated_amount', 0) for s in subscriptions):,.0f}/mo)" if subscriptions else "No recurring subscriptions detected"
    cashflow_summary = f"30d projection: ₹{cashflow.get('projected_balance_30d', 0):,.0f}" if cashflow else "N/A"
    trend_line = ""
    if trends:
        last = trends[-1]
        trend_line = f"Most recent month ({last['month']}): spent ₹{last['total_spent']:,.0f}, income ₹{last['total_income']:,.0f}"

    txn_ids = sorted([str(t.get("id")) for t in txns if t.get("id")])
    cache_data = {"txn_ids": txn_ids, "monthly_income": monthly_income}
    cache_key = hashlib.md5(json.dumps(cache_data, default=str).encode()).hexdigest()

    cached_insights = None
    if user and user.preferences:
        cached = user.preferences.get("insights_cache", {})
        if cached.get("hash") == cache_key:
            cached_insights = cached.get("insights", [])
            log.append("advisor_node: using cached insights (hash match)")

    if cached_insights:
        insights = cached_insights + insights
        log.append(f"advisor_node: {len(insights)} insights (cached)")
    else:
        prompt = f"""Financial Summary:
- Health Score: {health_score}/100
- Budget: {budget_summary}
- Anomalies: {anomaly_summary}
- Subscriptions: {sub_summary}
- Cash Flow: {cashflow_summary}
- {trend_line}
- Health Breakdown: {health_breakdown}

Generate personalized financial advice."""

        llm_insights = []
        try:
            text = await llm_invoke(prompt, INSIGHT_SYSTEM_PROMPT)
            sections = text.split("\n")
            current_section = "general"
            for line in sections:
                line = line.strip()
                if not line:
                    continue
                if "insight" in line.lower() or "action" in line.lower():
                    current_section = "actionable"
                elif "positive" in line.lower() or "good" in line.lower():
                    current_section = "positive"
                elif "recommend" in line.lower() or "next month" in line.lower():
                    current_section = "recommendation"

                llm_insights.append({
                    "type": current_section,
                    "text": line,
                })
        except Exception as e:
            llm_insights.append({"type": "general", "text": f"Advisor engine: {e}"})
            llm_insights.append({"type": "actionable", "text": f"Your savings rate is {utilization.get('savings_pct', 0):.0f}% — aim for 20%"})
            llm_insights.append({"type": "positive", "text": f"Health score {health_score}/100 is tracked and improving"})

        insights = llm_insights + insights

        if user:
            pref = user.preferences or {}
            pref["insights_cache"] = {"hash": cache_key, "insights": llm_insights}
            user.preferences = pref
            await db.commit()
            log.append("advisor_node: cached insights")

        log.append(f"advisor_node: {len(llm_insights)} insights generated by LLM")

    log.append(f"advisor_node: total {len(insights)} insights")
    log.append("advisor_node: END")
    return {
        **state,
        "insights": insights,
        "execution_log": log,
    }
