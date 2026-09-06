import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image as PILImage
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Image

ALLOWED_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}

_CANONICAL_CONTENT_TYPES = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/webp": "image/webp",
}


def save_image(db: Session, file: UploadFile) -> Image:
    image = save_image_bytes(
        db,
        data=file.file.read(),
        content_type=file.content_type,
        original_name=file.filename,
    )
    db.commit()
    db.refresh(image)
    return image


def save_image_bytes(
    db: Session,
    *,
    data: bytes,
    content_type: str | None,
    original_name: str | None = None,
) -> Image:
    raw_content_type = (content_type or "").lower()
    canonical_type = _CANONICAL_CONTENT_TYPES.get(raw_content_type)
    extension = ALLOWED_CONTENT_TYPES.get(raw_content_type)
    if not extension or not canonical_type:
        raise HTTPException(status_code=400, detail="Unsupported image type. Allowed: PNG, JPG, WEBP")

    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {settings.max_upload_size_mb} MB")

    try:
        image = PILImage.open(io.BytesIO(data))
        image.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or unsupported image file")

    filename = f"{uuid.uuid4().hex}{extension}"
    storage_dir = Path(settings.storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filepath = storage_dir / filename
    filepath.write_bytes(data)

    image_record = Image(
        filename=filename,
        storage_path=str(filepath),
        original_name=original_name,
        content_type=canonical_type,
        size=len(data),
    )
    db.add(image_record)
    db.flush()
    return image_record


def get_image_or_404(db: Session, image_id: int) -> Image:
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
