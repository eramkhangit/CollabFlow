from app.core.database import Base
from sqlalchemy import Column, String, Integer, DateTime,Boolean,Enum, URL
from functools import func
import enum

class UserRole(str, enum.Enum):
    USER='user'
    ADMIN='admin'
    DEVELOPER='developer'

class User(Base):
    __tablename__='user'

    id=Column(Integer,index=True, primary_key=True)
    user_name=Column(String(255), unique=True)
    email=Column(String(250), unique=True, nullable=False, index=True)
    password=Column(String(200), unique=True, nullable=False)
    role=Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    avtar_url=Column(URL, nullable=False)
    is_active=Column(Boolean, default=True, nullable=False)
    is_verified=Column(Boolean, default=False, nullable=False)

    created_at=Column(DateTime(timezone=True), server_default=func.now() )
    updated_at=Column(DateTime(timezone=True), onupdate=func.now())
    last_login=Column(DateTime(timezone=True), nullable=True)

    def has_role(self, role:UserRole):
        return self.role == role

    def __repr__(self):
        return f'{self.user_name} and {self.email}'