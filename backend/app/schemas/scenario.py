from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ScenarioSimulate(BaseModel):
    scenario_type: str
    inputs: dict


class ScenarioResponse(BaseModel):
    id: UUID
    name: str
    scenario_type: str
    inputs: dict | None = None
    projected_impact: dict | None = None
    recommendation: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True
