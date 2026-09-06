from datetime import date, datetime
from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums (values are stored in the database as strings)
# ---------------------------------------------------------------------------


class TaskStatus(str, Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    qa = "qa"
    blocked = "blocked"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class SprintStatus(str, Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


# ---------------------------------------------------------------------------
# Description content blocks
# ---------------------------------------------------------------------------


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    content: str


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    image_id: int


DescriptionBlock = Annotated[Union[TextBlock, ImageBlock], Field(discriminator="type")]


# ---------------------------------------------------------------------------
# Assignees
# ---------------------------------------------------------------------------


class AssigneeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    role: Optional[str] = None
    note: Optional[str] = None


class AssigneeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[str] = None
    note: Optional[str] = None


class AssigneeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Sprints
# ---------------------------------------------------------------------------


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    status: SprintStatus = SprintStatus.planned
    description: Optional[str] = None


class SprintUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SprintStatus] = None
    description: Optional[str] = None


class SprintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    end_date: date
    status: str
    description: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


class TaskLinkIn(BaseModel):
    label: Optional[str] = None
    url: str = Field(min_length=1, max_length=2000)


class TaskLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    label: Optional[str] = None
    url: str


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    text: str
    created_at: datetime


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    event_type: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    assignee_id: int
    description: List[DescriptionBlock] = Field(default_factory=list)
    priority: Optional[Priority] = None
    sprint_id: Optional[int] = None
    deadline: Optional[date] = None
    tag_ids: List[int] = Field(default_factory=list)
    links: List[TaskLinkIn] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[List[DescriptionBlock]] = None
    assignee_id: Optional[int] = None
    priority: Optional[Priority] = None
    sprint_id: Optional[int] = None
    deadline: Optional[date] = None
    tag_ids: Optional[List[int]] = None
    links: Optional[List[TaskLinkIn]] = None


class StatusChangeRequest(BaseModel):
    status: TaskStatus
    blocking_reason: Optional[str] = None


class AddToBoardRequest(BaseModel):
    status: TaskStatus = TaskStatus.backlog


class TaskSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    assignee_id: Optional[int] = None
    assignee: Optional[AssigneeOut] = None
    status: str
    priority: Optional[str] = None
    sprint_id: Optional[int] = None
    sprint: Optional[SprintOut] = None
    deadline: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    blocked_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None
    previous_status: Optional[str] = None
    is_on_board: bool
    is_archived: bool
    source: str = "manual"
    is_inbox: bool = False
    telegram_metadata: Optional[dict] = None
    tags: List[TagOut] = []


class TaskDetailOut(TaskSummaryOut):
    description: List[DescriptionBlock] = []
    links: List[TaskLinkOut] = []
    comments: List[CommentOut] = []
    history: List[HistoryOut] = []


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: Optional[str] = None
    content_type: str
    size: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Telegram intake
# ---------------------------------------------------------------------------


class TelegramPhotoIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)  # base64-encoded image bytes


class TelegramIntakeRequest(BaseModel):
    message_id: int
    chat_id: int
    sender_user_id: int
    sender_name: Optional[str] = None
    received_at: Optional[datetime] = None
    media_group_id: Optional[str] = None
    text: Optional[str] = None
    photos: List[TelegramPhotoIn] = Field(default_factory=list)


class TelegramIntakeResponse(BaseModel):
    task_id: int
    created: bool


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------


class PromptGenerateRequest(BaseModel):
    source_text: str = ""
    role: str = "General Development Task"
    title: Optional[str] = None
    links: Optional[str] = None
    context: Optional[str] = None


class PromptGenerateResponse(BaseModel):
    generated_prompt: str
    role: str


class PromptDraftCreate(BaseModel):
    source_text: str = ""
    role: str = "General Development Task"
    title: Optional[str] = None
    links: Optional[str] = None
    context: Optional[str] = None
    generated_prompt: str = ""
    ru_text: Optional[str] = None
    en_text: Optional[str] = None


class PromptDraftUpdate(BaseModel):
    source_text: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None
    links: Optional[str] = None
    context: Optional[str] = None
    generated_prompt: Optional[str] = None
    ru_text: Optional[str] = None
    en_text: Optional[str] = None


class PromptDraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_text: str
    role: str
    title: Optional[str] = None
    links: Optional[str] = None
    context: Optional[str] = None
    generated_prompt: str
    ru_text: Optional[str] = None
    en_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
