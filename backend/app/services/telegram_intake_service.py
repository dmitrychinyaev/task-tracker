import base64
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import HistoryEventType, TaskSource, TaskStatus, utcnow
from app.models import Task
from app.schemas import TelegramIntakeRequest, TelegramIntakeResponse
from app.services import image_service
from app.services.task_service import description_to_text, record_history

DEFAULT_INBOX_TITLE = "Задача из Telegram - разобрать"


def _dedup_key(payload: TelegramIntakeRequest) -> str:
    if payload.media_group_id:
        return f"telegram:{payload.chat_id}:{payload.media_group_id}"
    return f"telegram:{payload.chat_id}:{payload.message_id}"


def _build_metadata(payload: TelegramIntakeRequest) -> dict:
    received_at = payload.received_at or utcnow()
    metadata = {
        "sender_user_id": payload.sender_user_id,
        "chat_id": payload.chat_id,
        "message_id": payload.message_id,
        "received_at": received_at.isoformat() if isinstance(received_at, datetime) else str(received_at),
    }
    if payload.sender_name:
        metadata["sender_name"] = payload.sender_name
    if payload.media_group_id:
        metadata["media_group_id"] = payload.media_group_id
    return metadata


def _save_photos(db: Session, payload: TelegramIntakeRequest) -> list[dict]:
    blocks: list[dict] = []
    for photo in payload.photos:
        try:
            data = base64.b64decode(photo.content, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image payload")
        image = image_service.save_image_bytes(
            db,
            data=data,
            content_type=photo.content_type,
            original_name=photo.filename,
        )
        blocks.append({"type": "image", "image_id": image.id})
    return blocks


def handle_telegram_intake(db: Session, payload: TelegramIntakeRequest) -> TelegramIntakeResponse:
    if settings.telegram_allowed_user_ids and payload.sender_user_id not in settings.telegram_allowed_user_ids:
        raise HTTPException(status_code=403, detail="Sender is not allowed to create tasks")

    text = (payload.text or "").strip()
    if not text and not payload.photos:
        raise HTTPException(status_code=400, detail="Message has no text or photos")

    dedup_key = _dedup_key(payload)
    existing = db.query(Task).filter(Task.telegram_dedup_key == dedup_key).first()

    photo_blocks = _save_photos(db, payload)

    if existing:
        # Append new photos from the same media group (or re-delivery) to the existing task.
        if photo_blocks:
            blocks = list(existing.description or [])
            existing_ids = {b.get("image_id") for b in blocks if isinstance(b, dict) and b.get("type") == "image"}
            for block in photo_blocks:
                if block["image_id"] not in existing_ids:
                    blocks.append(block)
            existing.description = blocks
            existing.updated_at = utcnow()
            db.commit()
            db.refresh(existing)
        return TelegramIntakeResponse(task_id=existing.id, created=False)

    title = DEFAULT_INBOX_TITLE
    blocks: list[dict] = []
    if text:
        blocks.append({"type": "text", "content": text})
    blocks.extend(photo_blocks)

    task = Task(
        title=title,
        assignee_id=None,
        description=blocks,
        description_text=description_to_text(blocks),
        status=TaskStatus.BACKLOG,
        source=TaskSource.TELEGRAM,
        is_inbox=True,
        is_on_board=False,
        is_archived=False,
        telegram_metadata=_build_metadata(payload),
        telegram_dedup_key=dedup_key,
    )
    db.add(task)
    db.flush()
    record_history(db, task, HistoryEventType.INBOX_CREATED, "inbox", None, "true")
    db.commit()
    db.refresh(task)
    return TelegramIntakeResponse(task_id=task.id, created=True)
