from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.enums import HistoryEventType, TaskStatus, utcnow
from app.models import Assignee, Sprint, Tag, Task, TaskHistory, TaskLink
from app.schemas import TaskCreate, TaskUpdate


def description_to_text(blocks) -> str:
    parts = []
    for block in blocks or []:
        if isinstance(block, dict) and block.get("type") == "text":
            content = block.get("content")
            if content:
                parts.append(content)
    return "\n".join(parts)


def _blocks_to_dicts(blocks) -> list[dict]:
    return [block.model_dump() for block in blocks]


def record_history(db: Session, task: Task, event_type: str, field_name=None, old_value=None, new_value=None) -> None:
    db.add(
        TaskHistory(
            task_id=task.id,
            event_type=event_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
        )
    )


def _fmt(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _set_tags(db: Session, task: Task, tag_ids: list[int], record: bool = False) -> None:
    existing = {t.id for t in task.tags}
    new = set(tag_ids)

    for tag_id in new - existing:
        tag = db.get(Tag, tag_id)
        if not tag:
            raise HTTPException(status_code=400, detail=f"Tag {tag_id} not found")
        task.tags.append(tag)
        if record:
            record_history(db, task, HistoryEventType.TAG_ADDED, "tag", None, tag.name)

    for tag_id in existing - new:
        tag = db.get(Tag, tag_id)
        if tag is not None:
            task.tags.remove(tag)
            if record:
                record_history(db, task, HistoryEventType.TAG_REMOVED, "tag", tag.name, None)


def _set_links(db: Session, task: Task, links: list[dict]) -> None:
    task.links.clear()
    for link in links:
        task.links.append(TaskLink(label=link.get("label"), url=link.get("url")))


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def create_task(db: Session, data: TaskCreate) -> Task:
    if not db.get(Assignee, data.assignee_id):
        raise HTTPException(status_code=400, detail="Assignee not found")
    if data.sprint_id is not None and not db.get(Sprint, data.sprint_id):
        raise HTTPException(status_code=400, detail="Sprint not found")

    blocks = _blocks_to_dicts(data.description)
    task = Task(
        title=data.title,
        assignee_id=data.assignee_id,
        description=blocks,
        description_text=description_to_text(blocks),
        priority=data.priority.value if data.priority else None,
        sprint_id=data.sprint_id,
        deadline=data.deadline,
        status=TaskStatus.BACKLOG,
        is_on_board=False,
        is_archived=False,
    )
    db.add(task)
    db.flush()

    _set_tags(db, task, data.tag_ids, record=False)
    _set_links(db, task, [l.model_dump() for l in data.links])
    record_history(db, task, HistoryEventType.TASK_CREATED, "task", None, task.title)

    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    fields = data.model_fields_set

    if "title" in fields and data.title is not None and data.title != task.title:
        record_history(db, task, HistoryEventType.TITLE_CHANGED, "title", task.title, data.title)
        task.title = data.title

    if "description" in fields and data.description is not None:
        blocks = _blocks_to_dicts(data.description)
        task.description = blocks
        task.description_text = description_to_text(blocks)
        record_history(db, task, HistoryEventType.DESCRIPTION_CHANGED, "description", None, None)

    if "assignee_id" in fields and data.assignee_id is not None and data.assignee_id != task.assignee_id:
        if not db.get(Assignee, data.assignee_id):
            raise HTTPException(status_code=400, detail="Assignee not found")
        record_history(db, task, HistoryEventType.ASSIGNEE_CHANGED, "assignee", _fmt(task.assignee_id), _fmt(data.assignee_id))
        task.assignee_id = data.assignee_id

    if "priority" in fields:
        new_priority = data.priority.value if data.priority else None
        if new_priority != task.priority:
            record_history(db, task, HistoryEventType.PRIORITY_CHANGED, "priority", task.priority, new_priority)
            task.priority = new_priority

    if "sprint_id" in fields and data.sprint_id != task.sprint_id:
        if data.sprint_id is not None and not db.get(Sprint, data.sprint_id):
            raise HTTPException(status_code=400, detail="Sprint not found")
        record_history(db, task, HistoryEventType.SPRINT_CHANGED, "sprint", _fmt(task.sprint_id), _fmt(data.sprint_id))
        task.sprint_id = data.sprint_id

    if "deadline" in fields and data.deadline != task.deadline:
        record_history(db, task, HistoryEventType.DEADLINE_CHANGED, "deadline", _fmt(task.deadline), _fmt(data.deadline))
        task.deadline = data.deadline

    if "tag_ids" in fields and data.tag_ids is not None:
        _set_tags(db, task, data.tag_ids, record=True)

    if "links" in fields and data.links is not None:
        _set_links(db, task, [l.model_dump() for l in data.links])

    task.updated_at = utcnow()
    db.commit()
    db.refresh(task)
    return task


def change_status(db: Session, task: Task, new_status: str, blocking_reason: str | None = None) -> Task:
    old_status = task.status

    if new_status == old_status:
        db.commit()
        db.refresh(task)
        return task

    if new_status == TaskStatus.BLOCKED:
        if not blocking_reason or not blocking_reason.strip():
            raise HTTPException(status_code=400, detail="Blocking reason is required when moving a task to Blocked")
        task.blocked_reason = blocking_reason.strip()
        task.blocked_at = utcnow()
        task.previous_status = old_status
        task.status = new_status
        record_history(db, task, HistoryEventType.STATUS_CHANGED, "status", old_status, new_status)
        record_history(db, task, HistoryEventType.TASK_BLOCKED, "blocking_reason", None, task.blocked_reason)
    else:
        if old_status == TaskStatus.BLOCKED:
            record_history(db, task, HistoryEventType.TASK_UNBLOCKED, "blocking_reason", task.blocked_reason, None)
            task.blocked_reason = None
            task.blocked_at = None
            task.previous_status = None

        task.status = new_status
        record_history(db, task, HistoryEventType.STATUS_CHANGED, "status", old_status, new_status)

        if new_status == TaskStatus.DONE:
            task.completed_at = utcnow()
            task.is_archived = True
            record_history(db, task, HistoryEventType.TASK_COMPLETED, "status", old_status, new_status)

    task.updated_at = utcnow()
    db.commit()
    db.refresh(task)
    return task


def add_to_board(db: Session, task: Task, status: str) -> Task:
    record_history(db, task, HistoryEventType.ADDED_TO_BOARD, "board", None, "true")
    if status != task.status:
        record_history(db, task, HistoryEventType.STATUS_CHANGED, "status", task.status, status)
    task.status = status
    task.is_on_board = True
    task.updated_at = utcnow()
    db.commit()
    db.refresh(task)
    return task


def move_inbox_to_backlog(db: Session, task: Task) -> Task:
    if not task.is_inbox:
        raise HTTPException(status_code=400, detail="Task is not in the inbox")

    if not (task.title or "").strip():
        raise HTTPException(status_code=400, detail="Set a title before moving the task to backlog")
    if not task.assignee_id:
        raise HTTPException(status_code=400, detail="Assign an assignee before moving the task to backlog")

    record_history(db, task, HistoryEventType.INBOX_MOVED_TO_BACKLOG, "inbox", "true", "false")
    task.is_inbox = False
    task.status = TaskStatus.BACKLOG
    task.updated_at = utcnow()
    db.commit()
    db.refresh(task)
    return task
