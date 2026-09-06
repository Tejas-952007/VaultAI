"""Add structured PostgreSQL audit events.

Revision ID: 0003_audit_events
Revises: 0002_auth_sessions
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_audit_events"
down_revision = "0002_auth_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=80)),
        sa.Column("resource_id", sa.String(length=200)),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("request_id", sa.String(length=100)),
    )
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_employee_id", "audit_events", ["employee_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])


def downgrade() -> None:
    op.drop_table("audit_events")
