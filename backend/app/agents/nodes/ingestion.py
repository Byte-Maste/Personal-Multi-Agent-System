from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.state import SharedState
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.services.pdf_service import extract_text
from app.services.normalization_service import detect_source


async def ingestion_node(state: SharedState) -> SharedState:
    from app.agents.graph import get_graph_db
    log = state.get("execution_log", [])
    log.append("ingestion_node: START")

    db = get_graph_db()
    file_bytes: bytes | None = state.get("_file_bytes")
    file_name: str = state.get("_file_name", "")
    source: str = state.get("_source", "unknown")
    password: str | None = state.get("_password")

    user_id = state["user_id"]
    raw_text_preview = state.get("raw_text_preview", "")
    extracted_txns = state.get("extracted_transactions", [])

    if file_bytes:
        raw_text = extract_text(file_bytes, password)
        raw_text_preview = raw_text[:2000]
        detected_source = detect_source(raw_text, file_name) if source == "unknown" else source

        stmt = Statement(
            user_id=user_id,
            file_name=file_name,
            file_type=file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "",
            source=detected_source,
            raw_text=raw_text[:50000],
            processing_status="ingested",
        )
        db.add(stmt)
        await db.commit()
        await db.refresh(stmt)
        statement_ids = [str(stmt.id)]
        log.append(f"ingestion_node: created statement {stmt.id}")
    else:
        statement_ids = state.get("statement_ids", [])
        detected_source = source
        raw_text_preview = state.get("raw_text_preview", "")

    log.append("ingestion_node: END")
    return {
        **state,
        "statement_ids": statement_ids,
        "raw_text_preview": raw_text_preview,
        "extracted_transactions": extracted_txns,
        "execution_log": log,
        "category_summaries": state.get("category_summaries", {}),
        "monthly_summaries": state.get("monthly_summaries", {}),
        "trends": state.get("trends", []),
        "utilization_report": state.get("utilization_report", {}),
        "budget_alerts": state.get("budget_alerts", []),
        "rebalance_recommendations": state.get("rebalance_recommendations", []),
        "health_score": state.get("health_score", 0),
        "health_breakdown": state.get("health_breakdown", {}),
        "anomalies": state.get("anomalies", []),
        "subscriptions": state.get("subscriptions", []),
        "cashflow_forecast": state.get("cashflow_forecast", {}),
        "insights": state.get("insights", []),
        "goals_projection": state.get("goals_projection", []),
        "scenario_impact": state.get("scenario_impact", {}),
        "financial_twin_snapshot": state.get("financial_twin_snapshot", {}),
        "investment_readiness": state.get("investment_readiness", {}),
        "family_aggregation": state.get("family_aggregation", {}),
        "alerts_to_create": state.get("alerts_to_create", []),
        "response_to_user": state.get("response_to_user", ""),
    }
