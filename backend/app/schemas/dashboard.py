from pydantic import BaseModel

class DashboardResponse(BaseModel):
    health_score: int | None = None
    health_breakdown: dict | None = None
    monthly_savings: float | None = None
    budget_utilization: dict | None = None
    anomalies_count: int = 0
    upcoming_bills: list[dict] = []
    cashflow_forecast: dict | None = None
    top_insights: list[dict] = []
    alerts_count: int = 0
