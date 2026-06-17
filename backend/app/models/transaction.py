import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Boolean, Date, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    statement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("statements.id"), nullable=True)
    family_member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="transactions")
    statement = relationship("Statement")
    family_member = relationship("FamilyMember", back_populates="transactions")
    category = relationship("Category")

    __table_args__ = (
        Index("idx_tx_user_date", "user_id", "transaction_date"),
        Index("idx_tx_category", "user_id", "category_id"),
        Index("idx_tx_merchant", "user_id", "merchant"),
    )
