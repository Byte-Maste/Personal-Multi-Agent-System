from uuid import UUID
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class GoalCreate(BaseModel):
    title: str
    target_amount: float
    deadline: date | None = None
    priority: str | None = None


class GoalUpdate(BaseModel):
    current_amount: float | None = None
    status: str | None = None


class GoalResponse(BaseModel):
    id: UUID
    title: str
    target_amount: float
    current_amount: float
    deadline: date | None = None
    monthly_required: float | None = None
    priority: str | None = None
    status: str
    progress_pct: float = 0.0
    months_remaining: int | None = None
    feasible: bool = True
    created_at: str

    class Config:
        from_attributes = True
