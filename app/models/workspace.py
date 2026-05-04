from app.core.database import Base
from sqlalchemy import Column, String, DateTime,Enum ,ForeignKey,Text,Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import timezone, datetime
from sqlalchemy import UniqueConstraint

class WorkspaceRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

class Workspace(Base):
    __tablename__="workspace"

    id=Column(String(36),default=lambda: str(uuid.uuid4()) ,primary_key=True ,index=True ,nullable=False)
    owner_id=Column(String(36), ForeignKey("user.id"), nullable=False) 
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    owner = relationship("UserModel", back_populates="owned_workspaces")
    members = relationship("WorkspaceMembers", back_populates="workspace", cascade="all, delete-orphan")

    created_at=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_owner_workspace_name"),
    )

# juction table for user and workspace
class WorkspaceMembers(Base):
    __tablename__='workspace_memberships'

    __table_args__ = (
        UniqueConstraint("user_id", "workspace_id", name="uq_user_workspace"),
    ) 

    id=Column(String(36),default=lambda: str(uuid.uuid4()) ,primary_key=True ,index=True ,nullable=False)

    user_id=Column(String(36),ForeignKey("user.id"),nullable=False)   
    workspace_id=Column(String(36),ForeignKey("workspace.id"), nullable=False)
    is_active=Column(Boolean, default=True, nullable=False)
    # invited_by = Column(String(36), ForeignKey("user.id"), nullable=True)
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.MEMBER)

    user = relationship("UserModel", back_populates="workspace_memberships",lazy='selectin')
    workspace = relationship("Workspace", back_populates="members" , lazy="selectin")

    joined_at=Column(DateTime(timezone=True), server_default=func.now())
    left_at=Column(DateTime(timezone=True),nullable=True)