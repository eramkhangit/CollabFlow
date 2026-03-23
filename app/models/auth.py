from app.core.database import Base
from sqlalchemy import Column, String, Table, DateTime,Boolean,Enum,ForeignKey
from sqlalchemy.sql import func
import enum
import uuid
from sqlalchemy.orm import relationship
from app.models.project import project_members

# Junction Table (Association Table)
user_permissions=Table(
    'user_permissions',
    Base.metadata,
    Column('user_id',String(36), ForeignKey('user.id')),
    Column('permission_id',String(36), ForeignKey('permissions.id'))
)

class PermissionName(str, enum.Enum):
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    DELETE_USER = "delete:user"
    ADMIN_ACCESS = "admin:access"
    MANAGE_ROLES = "manage:roles"

# second table permission
class Permissions(Base):
    __tablename__='permissions'

    id=Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    permission_name=Column(Enum(PermissionName), default=PermissionName.ADMIN_ACCESS, nullable=False)
    
    users=relationship("UserModel",secondary=user_permissions,back_populates='permissions')

#  first table user
class UserRole(str, enum.Enum):
    USER='user'
    ADMIN='admin'
    DEVELOPER='developer'

class UserModel(Base):
    __tablename__='user'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    user_name=Column(String(255), unique=True)
    email=Column(String(250), unique=True, nullable=False, index=True)
    password=Column(String(255), nullable=False)
    role=Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    avatar_url=Column(String(500), nullable=True)

    is_active=Column(Boolean, default=True, nullable=False)
    is_verified=Column(Boolean, default=False, nullable=False)

    permissions=relationship('Permissions', secondary=user_permissions ,back_populates='users') # secondary : user for M2M

    assigned_tickets = relationship("Ticket", foreign_keys="Ticket.assigned_to", back_populates="assigned_user")

    created_tickets  = relationship("Ticket",foreign_keys="Ticket.created_by",back_populates="created_by_user")

    updated_tickets  = relationship("Ticket",foreign_keys="Ticket.updated_by",back_populates="updated_by_user")

    owned_projects=relationship("Project", back_populates="owner" )

    projects = relationship("Project", secondary=project_members, back_populates="members")


    created_at=Column(DateTime(timezone=True), server_default=func.now())
    updated_at=Column(DateTime(timezone=True), onupdate=func.now())
    last_login=Column(DateTime(timezone=True), nullable=True)

    def has_role(self, role:UserRole):
        return self.role == role

    def __repr__(self):
        return f'{self.user_name} and {self.email}'
    
    def has_permission(self, permission: PermissionName) -> bool:
        """Check if user has specific permission"""
        if self.role == UserRole.ADMIN:
            return True  # Admin has all permissions
        return any(p.permission_name == permission for p in self.permissions)