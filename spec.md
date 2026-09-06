# Bwanabet Local Task Tracker - Specification

## Purpose

The existing local single-user Task Tracker is extended with Telegram
Task Intake.

Supported intake paths: - manual task creation in the web application; -
raw task intake from a personal Telegram bot.

Telegram content is stored in a dedicated Inbox and manually reviewed
before becoming a normal Backlog task.

## Stack

-   Frontend: React + TypeScript + Vite
-   Backend: Python + FastAPI
-   Database: PostgreSQL
-   Infrastructure: Docker + Docker Compose
-   Telegram: separate Python bot service using Telegram Bot API
-   Attachments: existing local persistent task image storage

## Main pages

1.  Inbox
2.  Backlog
3.  Kanban
4.  Archive
5.  Reports
6.  Prompt Builder
7.  Settings

## Lifecycle

Telegram -\> Inbox -\> Backlog -\> Active Kanban -\> Done -\> Archive

Manual tasks may still be created directly in Backlog.

Inbox is not a Kanban column.

## Inbox

Telegram-created tasks: - start in Inbox; - use default title
`Задача из Telegram - разобрать`; - may temporarily have no assignee; -
preserve original text/caption without rewriting; - preserve all
supported photos; - have `source = telegram`.

Inbox provides: - task list; - text/photo preview; - `Разобрать`
action; - editing; - `Перенести в Backlog` action.

Before Inbox -\> Backlog, normal required fields apply: - title; -
assignee.

The transition must be recorded in task history.

## Telegram Intake

### Supported content

MVP accepts only: - direct text messages; - forwarded text messages; -
one photo with or without caption; - multiple photos in one Telegram
media group/album; - photo captions.

MVP does not support: - video; - voice; - audio; - documents; - PDF; -
stickers; - locations; - arbitrary files.

Unsupported content must not create an empty task.

### Task creation

Each accepted Telegram intake creates exactly one Inbox task.

Default title: `Задача из Telegram - разобрать`.

Do not automatically infer: - assignee; - tags; - sprint; - priority; -
deadline.

Store source as `telegram`.

### Photos

One photo -\> one Inbox task.

One Telegram media group -\> one Inbox task containing all photos.

The bot must: - detect `media_group_id`; - collect photos from the same
group; - preserve order; - download them; - send the intake to FastAPI.

The backend persists images using the existing attachment storage.

### Metadata and deduplication

Store useful Telegram metadata: - message ID; - chat ID; - sender user
ID; - media group ID when present; - received timestamp.

Forwarded-origin metadata is optional.

The integration must be idempotent where practical so Telegram retries
do not create duplicate tasks or attachments.

### Authorization

Only Telegram User IDs in `TELEGRAM_ALLOWED_USER_IDS` may create tasks.

Unauthorized messages must not create tasks.

### Bot response

After backend confirmation, reply concisely, for example:

`Задача #123 сохранена в Inbox.`

Do not report success before backend persistence succeeds.

## Architecture

Required path:

Telegram -\> Telegram Bot -\> FastAPI Backend -\> PostgreSQL / Local
File Storage

Telegram Bot must never access PostgreSQL directly.

Bot responsibilities: - receive updates; - validate allowed sender; -
collect media groups; - download photos; - call backend; - return
confirmation/error.

Business rules and persistence remain in the existing backend.

## Existing Task Tracker Behavior

Preserve existing: - Backlog; - Kanban statuses; - Archive; -
assignees; - multiple tags; - separate Sprint entity; - priorities and
deadlines; - comments; - structured history; - task links; - ordered
text/image descriptions; - PDF reports; - Prompt Builder.

Board statuses remain: - Backlog - To Do - In Progress - Review - QA -
Blocked - Done

Blocked tasks still require a blocking reason.

## Reports

Existing reports remain: - Single Task PDF - Kanban Snapshot - Sprint
Report - Activity Report by Date Range

Telegram-origin tasks participate normally after review.

## Explicitly Out of Scope

Do not add: - AI parsing of Telegram messages; - OCR; - voice
transcription; - video/document/PDF intake; - automatic
classification; - automatic assignee/tag/sprint/priority selection; -
Telegram group monitoring; - Telegram Business integration; - message
queues such as Kafka/RabbitMQ; - cloud deployment.

## UX

Inbox is optimized for fast triage: receive -\> inspect -\> refine -\>
move to Backlog.

Do not over-engineer the flow.
