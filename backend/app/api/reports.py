from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Image, Sprint, Task, TaskHistory
from app.services import report_service
from app.services.task_service import get_task_or_404

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/task/{task_id}")
def task_report(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)
    image_ids = [b.get("image_id") for b in (task.description or []) if b.get("type") == "image"]
    images_by_id = {}
    if image_ids:
        images_by_id = {img.id: img for img in db.query(Image).filter(Image.id.in_(image_ids)).all()}
    pdf = report_service.generate_task_pdf(task, images_by_id)
    return _pdf_response(pdf, f"task-{task.id}.pdf")


@router.get("/kanban")
def kanban_report(db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.is_on_board.is_(True), Task.is_archived.is_(False)).all()
    pdf = report_service.generate_kanban_pdf(tasks)
    return _pdf_response(pdf, "kanban-snapshot.pdf")


@router.get("/sprint/{sprint_id}")
def sprint_report(sprint_id: int, db: Session = Depends(get_db)):
    sprint = db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    tasks = db.query(Task).filter(Task.sprint_id == sprint_id).all()
    pdf = report_service.generate_sprint_pdf(sprint, tasks)
    return _pdf_response(pdf, f"sprint-{sprint.id}.pdf")


@router.get("/activity")
def activity_report(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=30)
    if start > end:
        raise HTTPException(status_code=400, detail="Start date must not be later than end date")

    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.max)

    rows = (
        db.query(TaskHistory, Task.title)
        .join(Task, TaskHistory.task_id == Task.id)
        .filter(TaskHistory.created_at >= start_dt, TaskHistory.created_at <= end_dt)
        .order_by(TaskHistory.created_at)
        .all()
    )
    events_with_titles = [(event, title) for event, title in rows]
    pdf = report_service.generate_activity_pdf(start, end, events_with_titles)
    return _pdf_response(pdf, "activity-report.pdf")
