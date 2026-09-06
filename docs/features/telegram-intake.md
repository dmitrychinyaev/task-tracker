# Feature: Telegram Task Intake

## Status

Implemented

## Problem

Project tasks frequently arrive through Telegram. Manual copying of
messages and screenshots into Task Tracker is slow and risks losing
tasks.

## Goal

Send or forward Telegram content to a dedicated bot and automatically
store it as an unprocessed Inbox task.

The bot is an intake channel, not a task-analysis system.

## Flow

Telegram message -\> Bot -\> FastAPI -\> Inbox -\> Manual review -\>
Backlog -\> Kanban -\> Archive

## Supported input

-   Direct text
-   Forwarded text
-   Single photo
-   Photo with caption
-   Multiple photos in one Telegram media group

## Unsupported input

-   Video
-   Voice
-   Audio
-   Documents/PDF
-   Stickers
-   Other files

## Created task

-   Default title: `Задача из Telegram - разобрать`
-   Initial state: Inbox
-   Source: telegram
-   Preserve original text/caption
-   Preserve all supported photos
-   No automatic assignee, priority, tags, sprint or deadline

## Inbox review

The user can inspect the raw task, click `Разобрать`, edit fields and
then `Перенести в Backlog`.

Inbox is not a Kanban column.

## Photos

One photo -\> one task.

One Telegram media group -\> one task.

All album photos are attached to that task in original order using
existing backend attachment storage.

## Security

Only IDs in `TELEGRAM_ALLOWED_USER_IDS` may create tasks.

The bot token is stored in `TELEGRAM_BOT_TOKEN`.

## Reliability

Prevent duplicate tasks from retried Telegram updates.

Do not create one task per photo in an album.

Confirm success only after backend persistence succeeds.

## Definition of Done

-   Bot starts through Docker Compose.
-   Existing application remains working.
-   Allowed user can send text.
-   Allowed user can forward text.
-   Text creates one Inbox task.
-   Single photo creates one Inbox task.
-   Caption is preserved.
-   Album creates one Inbox task.
-   All album photos are attached in order.
-   Unauthorized sender cannot create a task.
-   Unsupported media does not create an empty task.
-   Retried update does not create duplicate task.
-   Inbox task may exist without assignee.
-   User can review it.
-   Inbox -\> Backlog enforces normal required fields.
-   Inbox -\> Backlog is recorded in history.
-   Existing Kanban, reports and PDF behavior remain working.
-   Tests pass.

## Implementation Notes

- Implemented date: 2026-08-30
- Backend endpoint: `POST /api/telegram/intake`
- Bot library: `python-telegram-bot==22.8` (long polling)
- Docker service name: `bot`
- Migration IDs: `0002_telegram_intake.py`
- Known limitations:
  - The bot runs with long polling; no public webhooks are used.
  - Media-group order follows Telegram delivery order inside the debounce window.
  - Unsupported media is acknowledged with an error reply and does not create a task.
