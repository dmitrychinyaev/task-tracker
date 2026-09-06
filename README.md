# Bwanabet Local Task Tracker

Local single-user task tracker for managing work on the Bwanabet project.

## Stack

- React
- TypeScript
- Vite
- FastAPI
- PostgreSQL
- Docker
- Docker Compose

## Main Features

- Backlog
- Kanban board
- Inbox for Telegram-sourced tasks
- Archive
- Tags
- Assignees
- Sprints
- Comments
- Structured task history
- Images inside task descriptions
- PDF reports
- Prompt Builder for bilingual Russian/English task preparation
- Telegram bot intake (text and photos become Inbox tasks)

## Repository Structure

Suggested structure:

```text
.
├── frontend/
├── backend/
├── bot/
├── storage/
├── spec.md
├── rules.md
├── project_context.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Requirements

Install:

- Docker Desktop
- Docker Compose

No separate local PostgreSQL installation should be required.

## Start the Application

From the repository root:

```bash
docker compose up --build
```

After startup, open the frontend URL configured by the project.

Typical local addresses may be:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
```

The final implementation may use different ports if documented in `docker-compose.yml`.

## Stop the Application

```bash
docker compose down
```

## Important: Persistent Data

PostgreSQL data and uploaded task images must use Docker volumes.

Running:

```bash
docker compose down
```

must not remove task data.

Do not use volume deletion commands unless you intentionally want to erase local data.

## Environment Variables

Create `.env` from `.env.example` if required:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Typical settings may include:

```text
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
DATABASE_URL=
STORAGE_PATH=
TELEGRAM_BOT_TOKEN=
TELEGRAM_BACKEND_URL=
TELEGRAM_ALLOWED_USER_IDS=
TELEGRAM_MEDIA_GROUP_WINDOW=
```

Do not commit real secrets.

## Telegram Task Intake

The bot service receives Telegram messages through long polling and forwards
them to the FastAPI backend, which creates Inbox tasks. The bot never writes
to PostgreSQL directly.

Supported content:

- direct text messages;
- forwarded text messages;
- a single photo (with or without a caption);
- a photo album (one album becomes one task with all photos, in order).

Setup:

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Add the token and your Telegram user ID to `.env`:

```text
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_ALLOWED_USER_IDS=123456789
```

3. Start the application:

```bash
docker compose up --build
```

Allowed users can then send text or photos to the bot. Each accepted message
creates one Inbox task with the title `Задача из Telegram - разобрать`. Review
it in the Inbox, edit the title/assignee, and use `Перенести в Backlog`
(`Move to backlog`) when it is ready.

## Database Migrations

The backend should use Alembic.

Typical command inside the backend container:

```bash
alembic upgrade head
```

The final project should ideally run required migrations automatically during normal startup or document the exact command.

## PDF Reports

The application should support:

- single task PDF;
- current Kanban snapshot;
- sprint report;
- activity report by date range.

Single task PDF must include task images.

## Prompt Builder

Prompt Builder works without external AI API calls.

It generates a structured prompt for manual copying into another AI tool.

The generated prompt should request:
- Russian task description;
- English task description;
- acceptance criteria;
- relevant technical structure.

## Project Context

`project_context.md` contains optional Bwanabet domain context for AI tools and developers.

The application must not depend on this file at runtime.

## Development Source of Truth

Use:

1. `spec.md` for product behavior and functional requirements.
2. `rules.md` for development constraints.
3. `project_context.md` for Bwanabet domain context.
4. `README.md` for setup and local operation.

If implementation behavior conflicts with `spec.md`, `spec.md` should be treated as the product source of truth unless explicitly updated.
