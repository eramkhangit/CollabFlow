from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    USER='user'
    ADMIN='admin'
    DEVELOPER='developer'

class User(BaseModel):
    user_name:str = Field(..., min_length=5, description="Enter user name")
    email:EmailStr
    password:str = Field(..., min_length=8, max_length=50 , description="Enter password")
    role:UserRole= UserRole.USER
    avatar_url:Optional[str] = Field( description="Add user avatar url")
    is_active:bool = Field( default=True, description="User active status")
    is_verified:bool = Field(default=False, )

    created_at:datetime = Field(None, description="Auto-generated creation time")
    updated_at:Optional[datetime] = Field(None, description="Auto-generated update time")
    last_login:Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = {
        "from_attributes": True
    }

    @field_validator('password')
    def validate_password(cls, v):
        """Add custom password validation"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v
    
    @field_validator('user_name')
    def validate_username(cls, v):
        """Add username validation"""
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
class PermissionName(str, enum.Enum):
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    DELETE_USER = "delete:user"
    ADMIN_ACCESS = "admin:access"
    MANAGE_ROLES = "manage:roles"

class Permissions(BaseModel):
    permission_name:PermissionName=PermissionName.READ_USER 
    model_config = {
        "from_attributes": True
    }   