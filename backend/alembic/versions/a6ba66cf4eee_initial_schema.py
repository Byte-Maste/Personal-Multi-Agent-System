"""initial_schema

Revision ID: a6ba66cf4eee
Revises:
Create Date: 2026-06-17 17:24:32.658751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a6ba66cf4eee'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("monthly_income", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), server_default="INR"),
        sa.Column("emergency_fund_target", sa.Numeric(12, 2), nullable=True),
        sa.Column("risk_profile", sa.String(20), nullable=True),
        sa.Column("preferences", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(30), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("keywords", postgresql.JSONB, nullable=True),
        sa.Column("is_default", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "statements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("statement_period_start", sa.Date, nullable=True),
        sa.Column("statement_period_end", sa.Date, nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("meta_data", postgresql.JSONB, nullable=True),
        sa.Column("processing_status", sa.String(30), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "family_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("relationship", sa.String(50), nullable=True),
        sa.Column("monthly_income", sa.Numeric(12, 2), nullable=True),
        sa.Column("contribution_ratio", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column("monthly_required", sa.Numeric(12, 2), nullable=True),
        sa.Column("priority", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("meta_data", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("is_read", sa.Boolean, server_default=sa.text("false")),
        sa.Column("meta_data", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("merchant", sa.String(255), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("frequency", sa.String(20), nullable=True),
        sa.Column("last_charged", sa.Date, nullable=True),
        sa.Column("next_due", sa.Date, nullable=True),
        sa.Column("is_unused", sa.Boolean, server_default=sa.text("false")),
        sa.Column("usage_evidence", postgresql.JSONB, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scenario_type", sa.String(50), nullable=False),
        sa.Column("inputs", postgresql.JSONB, nullable=True),
        sa.Column("projected_impact", postgresql.JSONB, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "financial_health_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("savings_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("debt_ratio", sa.Numeric(5, 2), nullable=True),
        sa.Column("spending_consistency", sa.Numeric(5, 2), nullable=True),
        sa.Column("emergency_fund_months", sa.Numeric(5, 2), nullable=True),
        sa.Column("breakdown", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("period", sa.String(20), server_default="monthly"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("family_member_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("merchant", sa.String(255), nullable=True),
        sa.Column("raw_description", sa.Text, nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR"),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("is_recurring", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_anomaly", sa.Boolean, server_default=sa.text("false")),
        sa.Column("anomaly_reason", sa.Text, nullable=True),
        sa.Column("meta_data", postgresql.JSONB, nullable=True),
        sa.Column("is_deleted", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_tx_user_date", "transactions", ["user_id", "transaction_date"])
    op.create_index("idx_tx_category", "transactions", ["user_id", "category_id"])
    op.create_index("idx_tx_merchant", "transactions", ["user_id", "merchant"])


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("budgets")
    op.drop_table("financial_health_reports")
    op.drop_table("scenarios")
    op.drop_table("subscriptions")
    op.drop_table("alerts")
    op.drop_table("goals")
    op.drop_table("family_members")
    op.drop_table("statements")
    op.drop_table("categories")
    op.drop_table("users")
