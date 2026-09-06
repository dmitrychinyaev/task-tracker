"""add telegram intake fields to tasks

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tasks", "assignee_id", existing_type=sa.Integer(), nullable=True)

    op.add_column("tasks", sa.Column("source", sa.String(50), nullable=False, server_default="manual"))
    op.add_column("tasks", sa.Column("is_inbox", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("telegram_metadata", sa.JSON(), nullable=True))
    op.add_column("tasks", sa.Column("telegram_dedup_key", sa.String(500), nullable=True))
    op.create_unique_constraint("uq_tasks_telegram_dedup_key", "tasks", ["telegram_dedup_key"])


def downgrade() -> None:
    op.drop_constraint("uq_tasks_telegram_dedup_key", "tasks", type_="unique")
    op.drop_column("tasks", "telegram_dedup_key")
    op.drop_column("tasks", "telegram_metadata")
    op.drop_column("tasks", "is_inbox")
    op.drop_column("tasks", "source")
    op.alter_column("tasks", "assignee_id", existing_type=sa.Integer(), nullable=False)
