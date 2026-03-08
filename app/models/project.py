from app.core.database import Base
from sqlalchemy import Column, String, Text, DateTime,Enum, ForeignKey,Table
from sqlalchemy.sql import func
import enum
import uuid
from sqlalchemy.orm import relationship

# junction table
project_members=Table(
    'project_members',
    Base.metadata,
    Column('project_id',String(36), ForeignKey("project.id")),
    Column('user_id',String(36), ForeignKey("user.id"))
)

class ProjectStatus(str, enum.Enum):
    active='active'
    archived='archived'
    closed='closed'

class Project(Base):
    __tablename__='project'
    
    id=Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name=Column(String(200), nullable=False)
    status=Column(Enum(ProjectStatus), default=ProjectStatus.active , nullable=False) 
    description=Column(Text, nullable=True)
    owned_by=Column(String(36), ForeignKey('user.id'), nullable=False) 

    owner = relationship("User", foreign_keys=[owned_by], back_populates="owned_projects")
    members = relationship("User", secondary=project_members, back_populates="projects") 
    tickets = relationship("Ticket", back_populates="project")

    created_at=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at=Column(DateTime(timezone=True), nullable=True)
    due_date=Column(DateTime(timezone=True), nullable=True)