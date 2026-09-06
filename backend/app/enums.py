from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (DB-friendly)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TaskStatus:
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    QA = "qa"
    BLOCKED = "blocked"
    DONE = "done"

    ALL = [BACKLOG, TODO, IN_PROGRESS, REVIEW, QA, BLOCKED, DONE]


class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    ALL = [LOW, MEDIUM, HIGH, CRITICAL]


class SprintStatus:
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL = [PLANNED, ACTIVE, COMPLETED, CANCELLED]


class HistoryEventType:
    TASK_CREATED = "task_created"
    INBOX_CREATED = "inbox_created"
    INBOX_MOVED_TO_BACKLOG = "inbox_moved_to_backlog"
    TITLE_CHANGED = "title_changed"
    DESCRIPTION_CHANGED = "description_changed"
    STATUS_CHANGED = "status_changed"
    ASSIGNEE_CHANGED = "assignee_changed"
    SPRINT_CHANGED = "sprint_changed"
    PRIORITY_CHANGED = "priority_changed"
    DEADLINE_CHANGED = "deadline_changed"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    TASK_BLOCKED = "task_blocked"
    TASK_UNBLOCKED = "task_unblocked"
    TASK_COMPLETED = "task_completed"
    ADDED_TO_BOARD = "added_to_board"


class TaskSource:
    MANUAL = "manual"
    TELEGRAM = "telegram"

    ALL = [MANUAL, TELEGRAM]


class AssigneeRole:
    FRONTEND = "Frontend Developer"
    BACKEND = "Backend Developer"
    DESIGNER = "Designer"
    ANALYST = "Analyst"
    QA = "QA"
    OTHER = "Other"

    ALL = [FRONTEND, BACKEND, DESIGNER, ANALYST, QA, OTHER]
