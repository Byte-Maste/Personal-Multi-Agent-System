import uuid
from datetime import datetime, date
from sqlalchemy import String, Date, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    statement_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    statement_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="statements")
