import contextvars
from typing import Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import SharedState, empty_state
from app.agents.nodes.ingestion import ingestion_node
from app.agents.nodes.categorization import categorization_node
from app.agents.nodes.spending import spending_node
from app.agents.nodes.budget import budget_node
from app.agents.nodes.health_score import health_score_node
from app.agents.nodes.anomaly import anomaly_node
from app.agents.nodes.subscription import subscription_node
from app.agents.nodes.cashflow import cashflow_node
from app.agents.nodes.advisor import advisor_node
from app.agents.nodes.notification import notification_node

_db_context: contextvars.ContextVar[AsyncSession | None] = contextvars.ContextVar("graph_db", default=None)


def set_graph_db(db: AsyncSession) -> None:
    _db_context.set(db)


def get_graph_db() -> AsyncSession:
    db = _db_context.get()
    if db is None:
        raise RuntimeError("No DB session set in graph context")
    return db


def build_graph() -> StateGraph:
    builder = StateGraph(SharedState)

    builder.add_node("ingestion", ingestion_node)
    builder.add_node("categorization", categorization_node)
    builder.add_node("spending", spending_node)
    builder.add_node("budget", budget_node)
    builder.add_node("health_score", health_score_node)
    builder.add_node("anomaly", anomaly_node)
    builder.add_node("subscription", subscription_node)
    builder.add_node("cashflow", cashflow_node)
    builder.add_node("advisor", advisor_node)
    builder.add_node("notification", notification_node)

    builder.set_entry_point("ingestion")
    builder.add_edge("ingestion", "categorization")
    builder.add_edge("categorization", "spending")
    builder.add_edge("spending", "budget")
    builder.add_edge("budget", "health_score")
    builder.add_edge("health_score", "anomaly")
    builder.add_edge("anomaly", "subscription")
    builder.add_edge("subscription", "cashflow")
    builder.add_edge("cashflow", "advisor")
    builder.add_edge("advisor", "notification")
    builder.add_edge("notification", END)

    return builder.compile()


async def run_ingestion_pipeline(
    user_id: str,
    db: AsyncSession,
    file_bytes: bytes | None = None,
    file_name: str = "",
    source: str = "unknown",
    password: str | None = None,
) -> SharedState:
    graph = build_graph()
    state = empty_state()
    state["user_id"] = user_id
    state["_file_bytes"] = file_bytes
    state["_file_name"] = file_name
    state["_source"] = source
    state["_password"] = password

    set_graph_db(db)

    result = await graph.ainvoke(state)
    return result
