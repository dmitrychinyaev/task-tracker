# Bwanabet Local Task Tracker - Development Rules

## Sources of truth

1.  `rules.md` - mandatory engineering constraints.
2.  `spec.md` - current product behavior.
3.  `docs/features/*.md` - feature design/history.
4.  `project_context.md` - domain context.
5.  `README.md` - actual setup and operation.

## Agent operating rules

To avoid wasted work and tokens:

- Trust the provided context/status summary. Do not re-read files already
  marked as read or done; re-read only a file you are about to change.
- Read only the minimum contract needed (schema, config, route), not the
  whole codebase.
- Do not fetch web docs when the API is already known; fetch only when
  genuinely blocked.
- Keep verification minimal and non-redundant: one compile/lint/build pass.
- If the environment is known-incompatible (missing deps/tool), do not
  attempt to run tests; report the limitation instead.
- Do not re-read a file immediately after creating/editing it if it was
  created cleanly; verify only the final result.
- Create large files in chunks <= 6000 characters from the start.
- Do not redirect command output into temp files just to read them back;
  use direct terminal output.
- Start with the action that produces the result, not a full-project
  exploration.

## Preserve the existing application

This feature extends an already working and tested Task Tracker.

-   Do not rebuild the application from scratch.
-   Inspect existing code before changing architecture.
-   Do not rewrite unrelated modules.
-   Prefer additive migrations and backward-compatible changes.
-   Run existing tests before and after implementation.

## Fixed stack

-   React + TypeScript + Vite
-   FastAPI + Python
-   PostgreSQL
-   Docker + Docker Compose
-   Separate Python Telegram bot service

## Telegram service boundary

Allowed:

Telegram Bot -\> FastAPI Backend -\> PostgreSQL / Local Storage

Forbidden:

Telegram Bot -\> PostgreSQL

The bot must not duplicate backend task business logic.

## Telegram bot responsibilities

The bot may: - receive supported updates; - validate sender allowlist; -
collect photo media groups; - download Telegram photos; - call backend
intake API; - return success/failure.

The bot must not: - infer assignee, tags, sprint, priority or
deadline; - rewrite source text; - call external AI APIs; - write
directly to the database.

## Supported content

Accept only: - text; - forwarded text; - single photo; - photo
caption; - multi-photo media group.

Do not create tasks for unsupported media.

## Inbox rules

-   Inbox is a dedicated page/lifecycle state, not a Kanban column.
-   Telegram tasks start in Inbox.
-   Default title: `Задача из Telegram - разобрать`.
-   Inbox tasks may have no assignee.
-   Inbox -\> Backlog requires normal required fields, including title
    and assignee.
-   Record Inbox -\> Backlog in structured history.
-   Manual task creation behavior must remain unchanged.

## Media groups

Do not create one task per album photo.

Collect messages sharing `media_group_id` into one intake operation.

Preserve image order.

Use a simple bounded debounce/collection approach. Do not add Kafka or
RabbitMQ.

## Duplicate protection

Telegram delivery may retry.

Use stable Telegram identifiers to make intake idempotent where
practical.

Repeated updates must not create duplicate tasks/attachments.

## File handling

Reuse existing backend attachment storage.

Validate supported image type and size.

Use safe generated filenames and prevent path traversal.

Durable storage belongs to the backend, not the bot container.

## Secrets

Use environment variables:

`TELEGRAM_BOT_TOKEN`

`TELEGRAM_ALLOWED_USER_IDS`

Never commit or log the real bot token.

Provide placeholders in `.env.example`.

## Backend API

Add a dedicated Telegram intake endpoint.

It should accept: - text/caption; - Telegram metadata; - zero or more
photos.

Backend owns: - Inbox task creation; - attachments; - metadata; -
history; - deduplication; - created task ID response.

## Migrations

Use the existing migration mechanism.

Prefer additive schema changes.

Do not create a second Telegram-specific task model if the existing Task
entity can represent Inbox tasks.

## Docker

`docker compose up --build` must start the full application including
the Telegram bot.

Use Docker networking for bot -\> backend communication.

## Update delivery

For this local MVP, prefer long polling.

Do not add public webhooks, tunnels or reverse proxies solely for
Telegram.

## Error handling

Do not confirm success until backend confirms persistence.

Handle: - Telegram API failure; - backend unavailable; - unauthorized
sender; - unsupported media; - photo download failure; - duplicate
update.

Do not expose secrets in logs.

## Testing

Add tests for: - intake endpoint; - Inbox creation; - Inbox without
assignee; - Inbox -\> Backlog validation; - Telegram metadata; -
duplicate prevention; - single photo; - media group; - unauthorized
sender; - unsupported content; - backend failure.

Run all existing and new tests and fix regressions.

## No scope creep

Do not add AI parsing, OCR, voice/video/document processing, group
monitoring, cloud services or new authentication.
