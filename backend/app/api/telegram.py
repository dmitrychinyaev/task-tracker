from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TelegramIntakeRequest, TelegramIntakeResponse
from app.services import telegram_intake_service

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/intake", response_model=TelegramIntakeResponse, status_code=201)
def telegram_intake(payload: TelegramIntakeRequest, db: Session = Depends(get_db)):
    return telegram_intake_service.handle_telegram_intake(db, payload)
