from app.core.database import Base
from sqlalchemy import Column, String, DateTime,Enum ,ForeignKey,Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid

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



class Ticket(Base):
    __tablename__="ticket"

    id=Column(String(36),default=lambda: str(uuid.uuid4()) ,primary_key=True ,index=True ,nullable=False) # nullable=False: we cann't make it null
    ticket_name=Column(String(500),nullable=False)
    status=Column(Enum(TicketStatus), nullable=False, default=TicketStatus.todo)
    priority=Column(Enum(TicketPriority), nullable=False, default=TicketPriority.medium)
    description=Column(Text, nullable=True)
    # comment=Column(Text, nullable=True)
    ticket_type=Column(Enum(TicketType), nullable=False)

    # self-referential for sub-task
    parent_id=Column(String(36), ForeignKey('ticket.id'), nullable=True) 

    # who involve
    assigned_to=Column(String(36), ForeignKey("user.id"), nullable=True)
    created_by=Column(String(36), ForeignKey("user.id"), nullable=True)
    updated_by=Column(String(36), ForeignKey("user.id"), nullable=True)

    # belongs
    project_id=Column(String(36),ForeignKey('project.id'), nullable=False, index=True)

    # relations

    # connect to project model
    project = relationship("Project", back_populates="tickets") 
    assigned_user=relationship("UserModel", foreign_keys=[assigned_to] ,back_populates='assigned_tickets')
    created_by_user = relationship("UserModel", foreign_keys=[created_by],   back_populates="created_tickets") 
    updated_by_user = relationship("UserModel", foreign_keys=[updated_by],back_populates="updated_tickets")

    # self-referential
    # parent   = relationship("Ticket", remote_side=[id], back_populates="sub_tasks")
    # sub_tasks = relationship("Ticket", back_populates="parent")

    # Audit fields (timestamps)
    created_at=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at=Column(DateTime(timezone=True), nullable=True)
    due_date=Column(DateTime(timezone=True), nullable=True)


# class SubTicket(Base):
#     __tablename__='subticket'
#     id=Column()