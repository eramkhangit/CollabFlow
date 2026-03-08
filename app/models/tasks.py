from app.core.database import Base
from sqlalchemy import Column, String, Integer, DateTime,Enum, ForeignKey,Text
from sqlalchemy.sql import func
import enum
import uuid

class TaskStatus(str, enum.Enum):
    todo='todo'
    done='done'
    in_progress='progress'
    review='review'

class TaskPriority(str, enum.Enum):
    high='high'
    medium='medium'
    critical='critical'
    low='low'

class Tasks(Base):
    __tablename__="tasks"

    id=Column(String(100),default=lambda: str(uuid.uuid4()) ,primary_key=True ,index=True ,nullable=False) # nullable=False: we cann't make it null
    task_title=Column(String(500),nullable=False)
    status=Column(Enum(TaskStatus), nullable=False, default=TaskStatus.todo)
    priority=Column(Enum(TaskPriority), nullable=False, default=TaskPriority.medium)
    description=Column(Text, nullable=True)

    # who involve
    assigned_to=Column(Integer, ForeignKey("user.id"), nullable=True)
    created_by=Column(Integer, ForeignKey("user.id"), nullable=True)
    updated_by=Column(Integer, ForeignKey("user.id"), nullable=True)

    # belongs
    project_id=Column(Integer,ForeignKey('project.id'), nullable=False, index=True)
    team_id=Column(Integer,ForeignKey("team.id") ,nullable=True, index=True)
    parent_task_id=Column(Integer, ForeignKey('tasks.id'),nullable=True)

    # attachments
    
    # relations

    # Audit fields (timestamps)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
    updated_at=Column(DateTime(timezone=True), onupdate=func.now())
    completed_at=Column(DateTime(timezone=True), nullable=True)
    due_date=Column(DateTime(timezone=True), nullable=False)