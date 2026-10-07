import enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        Enum(TaskStatus, name="task_status"),
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
        index=True,
    )
    priority = Column(
        Enum(TaskPriority, name="task_priority"),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
        index=True,
    )

    # Simple label list, shown in TaskRow. Switch to a Label model +
    # join table later if labels need color/reuse/management UI.
    labels = Column(JSON, nullable=False, default=list)

    project_id = Column(
        CHAR(36), ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    
    assignee_id = Column(
        CHAR(36), ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    created_by_id = Column(
        CHAR(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True,
    )

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("UserModel", foreign_keys=[assignee_id])
    created_by = relationship("UserModel", foreign_keys=[created_by_id])

    is_deleted = Column(Boolean, nullable=False, default=False, server_default="0")
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        # Powers the TasksPage list query: project + status filter + sort
        Index("ix_tasks_project_status", "project_id", "status"),
        Index("ix_tasks_project_due_date", "project_id", "due_date"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"