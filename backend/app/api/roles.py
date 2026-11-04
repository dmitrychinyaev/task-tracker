from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assignee, Role
from app.schemas import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.name).all()


@router.post("", response_model=RoleRead, status_code=201)
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    role = Role(name=data.name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.patch("/{role_id}", response_model=RoleRead)
def update_role(role_id: int, data: RoleUpdate, db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    fields = data.model_fields_set
    if "name" in fields and data.name is not None:
        exists = db.query(Role).filter(Role.name == data.name, Role.id != role_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="Role with this name already exists")
        role.name = data.name

    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if db.query(Assignee).filter(Assignee.role_id == role_id).count():
        raise HTTPException(status_code=400, detail="Cannot delete role with assigned assignees")
    db.delete(role)
    db.commit()
    return Response(status_code=204)
