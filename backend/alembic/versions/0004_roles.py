"""roles dictionary

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-04

"""
from alembic import op
import sqlalchemy as sa

from app.enums import AssigneeRole

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.add_column(
        "assignees",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=True),
    )

    # Move the free-text roles into the dictionary (trimmed, no duplicates).
    op.execute(
        "INSERT INTO roles (name, created_at) "
        "SELECT DISTINCT TRIM(role), CURRENT_TIMESTAMP FROM assignees "
        "WHERE role IS NOT NULL AND TRIM(role) <> ''"
    )
    op.execute(
        "UPDATE assignees SET role_id = "
        "(SELECT id FROM roles WHERE roles.name = TRIM(assignees.role)) "
        "WHERE role IS NOT NULL AND TRIM(role) <> ''"
    )

    # A fresh database has no roles: seed the list the UI used to hardcode.
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM roles")).scalar() == 0:
        for name in AssigneeRole.ALL:
            bind.execute(
                sa.text("INSERT INTO roles (name, created_at) VALUES (:name, CURRENT_TIMESTAMP)"),
                {"name": name},
            )

    op.drop_column("assignees", "role")


def downgrade() -> None:
    op.add_column("assignees", sa.Column("role", sa.String(100), nullable=True))

    # `assignees.role` is narrower than `roles.name`, so long names are cut.
    op.execute(
        "UPDATE assignees SET role = "
        "(SELECT LEFT(name, 100) FROM roles WHERE roles.id = assignees.role_id)"
    )

    op.drop_column("assignees", "role_id")
    op.drop_table("roles")
