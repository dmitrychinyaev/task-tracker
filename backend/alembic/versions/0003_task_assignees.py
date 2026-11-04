"""task assignees many-to-many

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_assignees",
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("assignees.id", ondelete="CASCADE"), primary_key=True),
    )

    # Preserve the existing single assignee of every task.
    op.execute(
        "INSERT INTO task_assignees (task_id, assignee_id) "
        "SELECT id, assignee_id FROM tasks WHERE assignee_id IS NOT NULL"
    )

    op.drop_column("tasks", "assignee_id")


def downgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("assignees.id"), nullable=True),
    )

    # The single column cannot keep several assignees: keep the lowest assignee id.
    op.execute(
        "UPDATE tasks SET assignee_id = picked.assignee_id "
        "FROM (SELECT task_id, MIN(assignee_id) AS assignee_id FROM task_assignees GROUP BY task_id) AS picked "
        "WHERE tasks.id = picked.task_id"
    )

    op.drop_table("task_assignees")
