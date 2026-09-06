from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PromptDraft
from app.schemas import (
    PromptDraftCreate,
    PromptDraftOut,
    PromptDraftUpdate,
    PromptGenerateRequest,
    PromptGenerateResponse,
)
from app.services import prompt_service

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.post("/generate", response_model=PromptGenerateResponse)
def generate_prompt(data: PromptGenerateRequest):
    prompt = prompt_service.build_prompt(
        source_text=data.source_text,
        role=data.role,
        title=data.title,
        links=data.links,
        context=data.context,
    )
    return PromptGenerateResponse(generated_prompt=prompt, role=data.role)


@router.get("/drafts", response_model=list[PromptDraftOut])
def list_drafts(db: Session = Depends(get_db)):
    return db.query(PromptDraft).order_by(PromptDraft.updated_at.desc()).all()


@router.post("/drafts", response_model=PromptDraftOut, status_code=201)
def create_draft(data: PromptDraftCreate, db: Session = Depends(get_db)):
    draft = PromptDraft(**data.model_dump())
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.get("/drafts/{draft_id}", response_model=PromptDraftOut)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.get(PromptDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch("/drafts/{draft_id}", response_model=PromptDraftOut)
def update_draft(draft_id: int, data: PromptDraftUpdate, db: Session = Depends(get_db)):
    draft = db.get(PromptDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/drafts/{draft_id}", status_code=204)
def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.get(PromptDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    db.delete(draft)
    db.commit()
    return Response(status_code=204)
