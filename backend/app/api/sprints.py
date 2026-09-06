from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Sprint, Task
from app.schemas import SprintCreate, SprintOut, SprintUpdate

router = APIRouter(prefix="/api/sprints", tags=["sprints"])


def _validate_dates(start_date, end_date):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="Sprint end date must not be earlier than start date")


@router.get("", response_model=list[SprintOut])
def list_sprints(db: Session = Depends(get_db)):
    return db.query(Sprint).order_by(Sprint.start_date.desc()).all()


@router.post("", response_model=SprintOut, status_code=201)
def create_sprint(data: SprintCreate, db: Session = Depends(get_db)):
    if db.query(Sprint).filter(Sprint.name == data.name).first():
        raise HTTPException(status_code=400, detail="Sprint with this name already exists")
    _validate_dates(data.start_date, data.end_date)
    sprint = Sprint(
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        status=data.status.value,
        description=data.description,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.patch("/{sprint_id}", response_model=SprintOut)
def update_sprint(sprint_id: int, data: SprintUpdate, db: Session = Depends(get_db)):
    sprint = db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    fields = data.model_fields_set
    if "name" in fields and data.name is not None:
        exists = db.query(Sprint).filter(Sprint.name == data.name, Sprint.id != sprint_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="Sprint with this name already exists")
        sprint.name = data.name
    if "start_date" in fields:
        sprint.start_date = data.start_date
    if "end_date" in fields:
        sprint.end_date = data.end_date
    if "status" in fields and data.status is not None:
        sprint.status = data.status.value
    if "description" in fields:
        sprint.description = data.description

    _validate_dates(sprint.start_date, sprint.end_date)

    db.commit()
    db.refresh(sprint)
    return sprint


@router.delete("/{sprint_id}", status_code=204)
def delete_sprint(sprint_id: int, db: Session = Depends(get_db)):
    sprint = db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if db.query(Task).filter(Task.sprint_id == sprint_id).count():
        raise HTTPException(status_code=400, detail="Cannot delete a sprint that has tasks")
    db.delete(sprint)
    db.commit()
    return Response(status_code=204)
