from typing import TypedDict, Optional, Any
from datetime import date


class SharedState(TypedDict):
    user_id: str
    statement_ids: list[str]

    raw_text_preview: str
    extracted_transactions: list[dict]

    transactions: list[dict]
    category_id_map: dict[str, str]
    category_summaries: dict[str, float]

    monthly_summaries: dict[str, dict[str, float]]
    trends: list[dict]
    utilization_report: dict[str, Any]
    budget_alerts: list[dict]
    rebalance_recommendations: list[dict]
    health_score: int
    health_breakdown: dict[str, float]
    anomalies: list[dict]
    subscriptions: list[dict]
    cashflow_forecast: dict[str, Any]

    insights: list[dict]
    goals_projection: list[dict]
    scenario_impact: dict[str, Any]
    financial_twin_snapshot: dict[str, Any]
    investment_readiness: dict[str, Any]
    family_aggregation: dict[str, Any]

    alerts_to_create: list[dict]
    response_to_user: str
    execution_log: list[str]


def empty_state() -> SharedState:
    return SharedState(
        user_id="",
        statement_ids=[],
        raw_text_preview="",
        extracted_transactions=[],
        transactions=[],
        category_id_map={},
        category_summaries={},
        monthly_summaries={},
        trends=[],
        utilization_report={},
        budget_alerts=[],
        rebalance_recommendations=[],
        health_score=0,
        health_breakdown={},
        anomalies=[],
        subscriptions=[],
        cashflow_forecast={},
        insights=[],
        goals_projection=[],
        scenario_impact={},
        financial_twin_snapshot={},
        investment_readiness={},
        family_aggregation={},
        alerts_to_create=[],
        response_to_user="",
        execution_log=[],
    )
