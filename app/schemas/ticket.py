from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import enum

class TicketStatus(str, enum.Enum):
    todo='todo'
    done='done'
    in_progress='in_progress'
    review='review'

class TicketType(str, enum.Enum):
    bug='bug'
    task='task'
    sub_task='sub_task'
    story='story'
    epic='epic'

class TicketPriority(str, enum.Enum):
    high='high'
    medium='medium'
    critical='critical'
    low='low'

class Ticket(BaseModel):
    ticket_name:str=Field(..., min_length=3, max_length=500, description='Ticket title')
    status:TicketStatus =Field(default=TicketStatus.todo)
    priority:TicketPriority=Field(default=TicketPriority.medium)
    description: Optional[str] = Field(None, description='Explain brief about ticket')
    # parent_id:Optional[str] = Field(None, description='Ticket id')
    # assigned_to:Optional[str] = Field(None, description='Assigned id')
    # project_id:str =Field(..., description='Project id')
    ticket_type:TicketType=TicketType.task

    created_at:datetime = Field(None, description="Auto-generated creation time")
    updated_at:Optional[datetime] = Field(None, description="Auto-generated update time")
    completed_at:Optional[datetime] = Field(None, description="completed time")
    due_date:Optional[datetime] = Field(None, description="Due date")
