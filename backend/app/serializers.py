from app.schemas import (
    AssigneeOut,
    CommentOut,
    HistoryOut,
    SprintOut,
    TagOut,
    TaskDetailOut,
    TaskLinkOut,
    TaskSummaryOut,
)


def task_to_summary(task) -> TaskSummaryOut:
    return TaskSummaryOut(
        id=task.id,
        title=task.title,
        assignee_id=task.assignee_id,
        assignee=AssigneeOut.model_validate(task.assignee) if task.assignee else None,
        status=task.status,
        priority=task.priority,
        sprint_id=task.sprint_id,
        sprint=SprintOut.model_validate(task.sprint) if task.sprint else None,
        deadline=task.deadline,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        blocked_reason=task.blocked_reason,
        blocked_at=task.blocked_at,
        previous_status=task.previous_status,
        is_on_board=task.is_on_board,
        is_archived=task.is_archived,
        source=task.source or "manual",
        is_inbox=task.is_inbox,
        telegram_metadata=task.telegram_metadata,
        tags=[TagOut.model_validate(t) for t in task.tags],
    )


def task_to_detail(task) -> TaskDetailOut:
    summary = task_to_summary(task)
    comments = sorted(task.comments, key=lambda c: (c.created_at, c.id), reverse=True)
    history = sorted(task.history, key=lambda h: (h.created_at, h.id), reverse=True)
    return TaskDetailOut(
        **summary.model_dump(),
        description=task.description or [],
        links=[TaskLinkOut.model_validate(l) for l in sorted(task.links, key=lambda l: l.id)],
        comments=[CommentOut.model_validate(c) for c in comments],
        history=[HistoryOut.model_validate(h) for h in history],
    )
