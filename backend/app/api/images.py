from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ImageOut
from app.services import image_service

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("", response_model=ImageOut, status_code=201)
def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return image_service.save_image(db, file)


@router.get("/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    image = image_service.get_image_or_404(db, image_id)
    return FileResponse(image.storage_path, media_type=image.content_type)
