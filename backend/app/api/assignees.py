from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assignee, Role, Task
from app.schemas import AssigneeCreate, AssigneeOut, AssigneeUpdate

router = APIRouter(prefix="/api/assignees", tags=["assignees"])


def _check_role(db: Session, role_id: int | None) -> None:
    if role_id is not None and db.get(Role, role_id) is None:
        raise HTTPException(status_code=400, detail="Role not found")


@router.get("", response_model=list[AssigneeOut])
def list_assignees(db: Session = Depends(get_db)):
    return db.query(Assignee).order_by(Assignee.name).all()


@router.post("", response_model=AssigneeOut, status_code=201)
def create_assignee(data: AssigneeCreate, db: Session = Depends(get_db)):
    if db.query(Assignee).filter(Assignee.name == data.name).first():
        raise HTTPException(status_code=400, detail="Assignee with this name already exists")
    _check_role(db, data.role_id)
    assignee = Assignee(name=data.name, role_id=data.role_id, note=data.note)
    db.add(assignee)
    db.commit()
    db.refresh(assignee)
    return assignee


@router.patch("/{assignee_id}", response_model=AssigneeOut)
def update_assignee(assignee_id: int, data: AssigneeUpdate, db: Session = Depends(get_db)):
    assignee = db.get(Assignee, assignee_id)
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")

    fields = data.model_fields_set
    if "name" in fields and data.name is not None:
        exists = db.query(Assignee).filter(Assignee.name == data.name, Assignee.id != assignee_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="Assignee with this name already exists")
        assignee.name = data.name
    if "role_id" in fields:
        _check_role(db, data.role_id)
        assignee.role_id = data.role_id
    if "note" in fields:
        assignee.note = data.note

    db.commit()
    db.refresh(assignee)
    return assignee


@router.delete("/{assignee_id}", status_code=204)
def delete_assignee(assignee_id: int, db: Session = Depends(get_db)):
    assignee = db.get(Assignee, assignee_id)
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    if db.query(Task).filter(Task.assignees.any(Assignee.id == assignee_id)).count():
        raise HTTPException(status_code=400, detail="Cannot delete an assignee that has tasks")
    db.delete(assignee)
    db.commit()
    return Response(status_code=204)
