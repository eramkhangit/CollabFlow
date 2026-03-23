from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, ClassVar, Any
from datetime import datetime
import enum

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class UserRole(str, enum.Enum):
    USER='user'
    ADMIN='admin'
    DEVELOPER='developer'

class UserBase(BaseSchema):
    user_name:str = Field(..., min_length=5, description="Enter user name")
    email:EmailStr 
    password:str = Field(..., min_length=8, max_length=50 , description="Enter password")
    role:UserRole= UserRole.USER
    avatar_url:Optional[str] = Field(default=None, description="Add user avatar url")

class User(UserBase):
    # user_name:str = Field(..., min_length=5, description="Enter user name")
    # email:EmailStr 
    # password:str = Field(..., min_length=8, max_length=50 , description="Enter password")
    # role:UserRole= UserRole.USER
    # avatar_url:Optional[str] = Field( description="Add user avatar url")
    is_active:bool = Field( default=True, description="User active status")
    is_verified:bool = Field(default=False, )

    # created_at:datetime = Field(None, description="Auto-generated creation time")
    # updated_at:Optional[datetime] = Field(None, description="Auto-generated update time")
    # last_login:Optional[datetime] = Field(None, description="Last login timestamp")

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

class UserResponse(BaseSchema): 
    id: str                        
    user_name: str
    email: EmailStr
    role: UserRole
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
    from_attributes=True,
    json_schema_extra={
            "example": {
                "id": "c7b82f93-8877-459",
                "user_name": "johndoe",
                "email": "john@example.com",
                "role": "user",
                "avatar_url": None,
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None,
                "last_login": None
        }
    }
)

class PermissionName(str, enum.Enum):
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    DELETE_USER = "delete:user"
    ADMIN_ACCESS = "admin:access"
    MANAGE_ROLES = "manage:roles"

class Permissions(BaseSchema):
    permission_name:PermissionName=PermissionName.READ_USER 
    model_config = {
        "from_attributes": True
    }   
