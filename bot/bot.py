"""Telegram Task Intake bot.

Responsibilities (see rules.md / spec.md):
- receive supported updates via long polling;
- validate the sender against TELEGRAM_ALLOWED_USER_IDS;
- collect photo media groups so one album becomes one intake;
- download photos and forward them to the FastAPI intake endpoint;
- reply only after the backend confirms persistence.

The bot never talks to PostgreSQL directly and does not infer any task
business fields (assignee, tags, sprint, priority, deadline).
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
from typing import Any

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("telegram-bot")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
BACKEND_URL = os.environ.get("TELEGRAM_BACKEND_URL", "http://backend:8000").rstrip("/")
INTAKE_PATH = "/api/telegram/intake"
MEDIA_GROUP_WINDOW = float(os.environ.get("TELEGRAM_MEDIA_GROUP_WINDOW", "2"))

UNAUTHORIZED_REPLY = "У вас нет доступа к этому боту."
UNSUPPORTED_REPLY = "Этот тип сообщений не поддерживается. Отправьте текст или фото."
BACKEND_ERROR_REPLY = "Не удалось сохранить задачу. Попробуйте позже."
DUPLICATE_REPLY = "Сообщение уже обработано (задача #{task_id})."
SUCCESS_REPLY = "Задача #{task_id} сохранена в Inbox."


class IntakeError(Exception):
    """Raised when the backend rejects an intake request."""


def parse_allowed_user_ids(raw: str | None) -> set[int]:
    if not raw or not raw.strip():
        return set()
    raw = raw.strip()
    if raw.startswith("["):
        try:
            values = json.loads(raw)
            if isinstance(values, list):
                return {int(x) for x in values}
        except (ValueError, TypeError):
            logger.warning("Could not parse TELEGRAM_ALLOWED_USER_IDS as JSON: %s", raw)
    return {int(part) for part in raw.split(",") if part.strip()}


ALLOWED_USER_IDS = parse_allowed_user_ids(os.environ.get("TELEGRAM_ALLOWED_USER_IDS"))

# media_group_id -> pending album being collected
_pending: dict[str, dict[str, Any]] = {}
_pending_lock = asyncio.Lock()


def _base_payload(message: Any, sender: Any, chat_id: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "message_id": message.message_id,
        "chat_id": chat_id,
        "sender_user_id": sender.id,
        "received_at": message.date.isoformat(),
    }
    name = getattr(sender, "full_name", None) or getattr(sender, "username", None)
    if name:
        payload["sender_name"] = name
    if getattr(message, "media_group_id", None):
        payload["media_group_id"] = message.media_group_id
    return payload


async def _download_photo(message: Any) -> dict[str, str]:
    photo = message.photo[-1]
    file = await photo.get_file()
    buffer = io.BytesIO()
    await file.download_to_memory(out=buffer)
    return {
        "filename": f"{photo.file_unique_id}.jpg",
        "content_type": "image/jpeg",
        "content": base64.b64encode(buffer.getvalue()).decode("ascii"),
    }


async def _reply(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    reply_to_message_id: int | None,
    text: str,
) -> None:
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
        )
    except Exception:
        logger.exception("Failed to reply in chat %s", chat_id)


async def _authorize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user is None:
        return False
    if ALLOWED_USER_IDS and user.id not in ALLOWED_USER_IDS:
        chat_id = update.effective_chat.id if update.effective_chat else user.id
        reply_id = update.effective_message.message_id if update.effective_message else None
        await _reply(context, chat_id, reply_id, UNAUTHORIZED_REPLY)
        return False
    return True



async def _post_intake(
    context: ContextTypes.DEFAULT_TYPE,
    payload: dict[str, Any],
) -> dict[str, Any]:
    client: httpx.AsyncClient = context.bot_data["http"]
    response = await client.post(f"{BACKEND_URL}{INTAKE_PATH}", json=payload)
    if response.status_code in (200, 201):
        return response.json()

    detail = "unknown error"
    try:
        body = response.json()
        if isinstance(body.get("detail"), str):
            detail = body["detail"]
    except Exception:
        detail = response.text[:200] or detail
    raise IntakeError(f"{detail} (HTTP {response.status_code})")


async def _deliver(
    context: ContextTypes.DEFAULT_TYPE,
    payload: dict[str, Any],
    chat_id: int,
    reply_to_message_id: int,
) -> None:
    try:
        data = await _post_intake(context, payload)
    except IntakeError as exc:
        logger.error("Backend intake failed: %s", exc)
        await _reply(context, chat_id, reply_to_message_id, BACKEND_ERROR_REPLY)
        return
    except Exception:
        logger.exception("Unexpected backend intake failure")
        await _reply(context, chat_id, reply_to_message_id, BACKEND_ERROR_REPLY)
        return

    task_id = data.get("task_id")
    if data.get("created"):
        text = SUCCESS_REPLY.format(task_id=task_id)
    else:
        text = DUPLICATE_REPLY.format(task_id=task_id)
    await _reply(context, chat_id, reply_to_message_id, text)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorize(update, context):
        return
    text = (
        "Отправьте текст или фото (в том числе пересланное) — и я создам задачу в Inbox. "
        "Альбом из нескольких фото будет сохранён одной задачей."
    )
    await _reply(
        context,
        update.effective_chat.id,
        update.effective_message.message_id,
        text,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorize(update, context):
        return
    message = update.effective_message
    sender = update.effective_user
    chat_id = update.effective_chat.id
    payload = _base_payload(message, sender, chat_id)
    payload["text"] = message.text
    await _deliver(context, payload, chat_id, message.message_id)


async def _schedule_flush(
    context: ContextTypes.DEFAULT_TYPE,
    media_group_id: str,
) -> None:
    name = f"media_group:{media_group_id}"
    for job in context.job_queue.get_jobs_by_name(name):
        job.schedule_removal()
    context.job_queue.run_once(
        _flush_media_group,
        MEDIA_GROUP_WINDOW,
        name=name,
        data={"media_group_id": media_group_id},
    )


async def _flush_media_group(context: ContextTypes.DEFAULT_TYPE) -> None:
    media_group_id = context.job.data["media_group_id"]
    async with _pending_lock:
        entry = _pending.pop(media_group_id, None)
    if not entry:
        return

    payload = {
        "message_id": entry["message_id"],
        "chat_id": entry["chat_id"],
        "sender_user_id": entry["sender_user_id"],
        "received_at": entry["received_at"],
        "media_group_id": media_group_id,
        "photos": entry["photos"],
    }
    if entry.get("sender_name"):
        payload["sender_name"] = entry["sender_name"]
    if entry.get("caption"):
        payload["text"] = entry["caption"]

    await _deliver(context, payload, entry["chat_id"], entry["reply_to_message_id"])


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorize(update, context):
        return
    message = update.effective_message
    sender = update.effective_user
    chat_id = update.effective_chat.id
    media_group_id = getattr(message, "media_group_id", None)

    photo = await _download_photo(message)

    if not media_group_id:
        payload = _base_payload(message, sender, chat_id)
        if message.caption:
            payload["text"] = message.caption
        payload["photos"] = [photo]
        await _deliver(context, payload, chat_id, message.message_id)
        return

    async with _pending_lock:
        entry = _pending.get(media_group_id)
        if entry is None:
            entry = {
                "message_id": message.message_id,
                "chat_id": chat_id,
                "sender_user_id": sender.id,
                "sender_name": getattr(sender, "full_name", None) or getattr(sender, "username", None),
                "received_at": message.date.isoformat(),
                "reply_to_message_id": message.message_id,
                "caption": None,
                "photos": [],
            }
            _pending[media_group_id] = entry
        entry["photos"].append(photo)
        if message.caption and not entry["caption"]:
            entry["caption"] = message.caption

    await _schedule_flush(context, media_group_id)


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorize(update, context):
        return
    await _reply(
        context,
        update.effective_chat.id,
        update.effective_message.message_id,
        UNSUPPORTED_REPLY,
    )


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Error while handling an update", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_chat:
        await _reply(context, update.effective_chat.id, None, BACKEND_ERROR_REPLY)


async def _on_shutdown(application: Application) -> None:
    client = application.bot_data.get("http")
    if client:
        await client.aclose()


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")

    application = Application.builder().token(BOT_TOKEN).build()
    application.bot_data["http"] = httpx.AsyncClient(timeout=60.0)
    application.bot_data["allowed_user_ids"] = ALLOWED_USER_IDS

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & ~filters.TEXT & ~filters.PHOTO,
            handle_unsupported,
        )
    )
    application.add_error_handler(handle_error)
    application.post_shutdown = _on_shutdown

    logger.info("Starting Telegram bot (long polling)")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()

