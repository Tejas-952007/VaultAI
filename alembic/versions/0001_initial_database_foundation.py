"""Create VaultAI database foundation tables.

Revision ID: 0001_initial_database_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_database_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name"))
    op.create_table("positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name"))
    op.create_table("permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code"))
    op.create_table("employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL")),
        sa.Column("position_id", sa.Integer(), sa.ForeignKey("positions.id", ondelete="SET NULL")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id"))
    op.create_table("position_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("position_id", sa.Integer(), sa.ForeignKey("positions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allowed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.UniqueConstraint("position_id", "permission_id", name="uq_position_permission"))
    op.create_table("employee_permission_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id", "permission_id", name="uq_employee_permission_override"))
    for table, columns in {
        "departments": ["name"],
        "positions": ["name", "department_id"],
        "permissions": ["code"],
        "employees": ["employee_id", "department_id", "position_id"],
        "position_permissions": ["position_id", "permission_id"],
        "employee_permission_overrides": ["employee_id", "permission_id"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column], unique=False)


def downgrade() -> None:
    for table in ("employee_permission_overrides", "position_permissions", "employees", "permissions", "positions", "departments"):
        op.drop_table(table)
