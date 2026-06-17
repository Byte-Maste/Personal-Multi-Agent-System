import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, Date, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_charged: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_unused: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
