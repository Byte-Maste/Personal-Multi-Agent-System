import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, Numeric, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class FinancialHealthReport(Base):
    __tablename__ = "financial_health_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    savings_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    debt_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    spending_consistency: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    emergency_fund_months: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
