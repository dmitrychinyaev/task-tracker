from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Tag, Task
from app.schemas import (
    AddToBoardRequest,
    CommentCreate,
    CommentOut,
    StatusChangeRequest,
    TaskCreate,
    TaskDetailOut,
    TaskSummaryOut,
    TaskUpdate,
)
from app.serializers import task_to_detail, task_to_summary
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _apply_location(query, location: str | None):
    if location == "inbox":
        return query.filter(Task.is_inbox.is_(True), Task.is_archived.is_(False))
    if location == "backlog":
        return query.filter(Task.is_inbox.is_(False), Task.is_on_board.is_(False), Task.is_archived.is_(False))
    if location == "board":
        return query.filter(Task.is_on_board.is_(True), Task.is_archived.is_(False))
    if location == "archive":
        return query.filter(Task.is_archived.is_(True))
    return query


@router.get("", response_model=list[TaskSummaryOut])
def list_tasks(
    location: str | None = None,
    assignee_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    sprint_id: int | None = None,
    tag_id: int | None = None,
    search: str | None = None,
    deadline_from: date | None = None,
    deadline_to: date | None = None,
    completed_from: date | None = None,
    completed_to: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    query = _apply_location(query, location)

    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if sprint_id is not None:
        query = query.filter(Task.sprint_id == sprint_id)
    if tag_id is not None:
        query = query.filter(Task.tags.any(Tag.id == tag_id))
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(Task.title.ilike(like), Task.description_text.ilike(like)))
    if deadline_from is not None:
        query = query.filter(Task.deadline >= deadline_from)
    if deadline_to is not None:
        query = query.filter(Task.deadline <= deadline_to)
    if completed_from is not None:
        query = query.filter(Task.completed_at >= datetime.combine(completed_from, time.min))
    if completed_to is not None:
        query = query.filter(Task.completed_at <= datetime.combine(completed_to, time.max))

    tasks = query.order_by(Task.updated_at.desc()).all()
    return [task_to_summary(t) for t in tasks]


@router.post("", response_model=TaskDetailOut, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = task_service.create_task(db, data)
    return task_to_detail(task)


@router.get("/{task_id}", response_model=TaskDetailOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    return task_to_detail(task)


@router.patch("/{task_id}", response_model=TaskDetailOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    task = task_service.update_task(db, task, data)
    return task_to_detail(task)


@router.post("/{task_id}/move", response_model=TaskDetailOut)
def move_task(task_id: int, data: StatusChangeRequest, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    task = task_service.change_status(db, task, data.status.value, data.blocking_reason)
    return task_to_detail(task)


@router.post("/{task_id}/add-to-board", response_model=TaskDetailOut)
def add_to_board(task_id: int, data: AddToBoardRequest, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    task = task_service.add_to_board(db, task, data.status.value)
    return task_to_detail(task)


@router.post("/{task_id}/move-to-backlog", response_model=TaskDetailOut)
def move_to_backlog(task_id: int, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    task = task_service.move_inbox_to_backlog(db, task)
    return task_to_detail(task)


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(task_id: int, data: CommentCreate, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    comment = Comment(task_id=task.id, text=data.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = task_service.get_task_or_404(db, task_id)
    db.delete(task)
    db.commit()
    return Response(status_code=204)
