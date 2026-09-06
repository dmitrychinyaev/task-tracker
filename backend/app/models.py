from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import TaskStatus, utcnow

task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Assignee(Base):
    __tablename__ = "assignees"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    role = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    tasks = relationship("Task", back_populates="assignee")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="planned")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    tasks = relationship("Task", back_populates="sprint")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    # Ordered list of content blocks: {"type": "text", "content": "..."}
    # or {"type": "image", "image_id": 1}.
    description = Column(JSON, nullable=False, default=list)
    # Plain-text projection of text blocks, used for search.
    description_text = Column(Text, nullable=False, default="")

    assignee_id = Column(Integer, ForeignKey("assignees.id"), nullable=True)
    status = Column(String(50), nullable=False, default=TaskStatus.BACKLOG)
    priority = Column(String(50), nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    deadline = Column(Date, nullable=True)

    source = Column(String(50), nullable=False, default="manual")
    is_inbox = Column(Boolean, nullable=False, default=False)
    telegram_metadata = Column(JSON, nullable=True)
    telegram_dedup_key = Column(String(500), nullable=True, unique=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    blocked_reason = Column(Text, nullable=True)
    blocked_at = Column(DateTime, nullable=True)
    previous_status = Column(String(50), nullable=True)

    is_on_board = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)

    assignee = relationship("Assignee", back_populates="tasks", lazy="selectin")
    sprint = relationship("Sprint", back_populates="tasks", lazy="selectin")
    tags = relationship("Tag", secondary=task_tags, lazy="selectin")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    links = relationship("TaskLink", back_populates="task", cascade="all, delete-orphan")


class TaskLink(Base):
    __tablename__ = "task_links"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(255), nullable=True)
    url = Column(String(2000), nullable=False)

    task = relationship("Task", back_populates="links")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    task = relationship("Task", back_populates="comments")


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    task = relationship("Task", back_populates="history")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False, unique=True)
    storage_path = Column(String(2000), nullable=False)
    original_name = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class PromptDraft(Base):
    __tablename__ = "prompt_drafts"

    id = Column(Integer, primary_key=True)
    source_text = Column(Text, nullable=False, default="")
    role = Column(String(100), nullable=False, default="General Development Task")
    title = Column(String(500), nullable=True)
    links = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    generated_prompt = Column(Text, nullable=False, default="")
    ru_text = Column(Text, nullable=True)
    en_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
