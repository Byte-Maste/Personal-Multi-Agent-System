from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel


class FamilyMemberCreate(BaseModel):
    name: str
    relation: str | None = None
    monthly_income: float | None = None


class FamilyMemberUpdate(BaseModel):
    monthly_income: float | None = None
    relation: str | None = None


class FamilyMemberResponse(BaseModel):
    id: UUID
    name: str
    relation: str | None = None
    monthly_income: float | None = None
    contribution_ratio: float | None = None

    class Config:
        from_attributes = True


class FamilyAggregation(BaseModel):
    total_income: float
    member_count: int
    members: list[FamilyMemberResponse]
