from pydantic import BaseModel, Field,ConfigDict, field_validator
from typing import Optional
import enum
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class WorkspaceRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

class WorkspaceSchema(BaseSchema):
    owner_id:str=Field(..., description="Owner id")
    name:str=Field(..., description="Workspace name")
    description:Optional[str]=Field(default=None ,description="Description about workspace")
    is_active:bool=Field(default=True, description="Workspace active or not")

    @field_validator("name")
    def validate_name(cls, value: str):
        if not value or not value.strip():
            raise ValueError("Workspace name cannot be empty")
        
        if not (3 <= len(value) <= 100) :
            raise ValueError("Workspace name should be minimum 3 and maximum 100 characters")

        return value.strip()

class WorkspaceMembersSchema(BaseSchema):
    user_id:str=Field(..., description="User id")
    workspace_id:str=Field(..., description="workspace id")
    is_active:bool=Field(default=True, description="Workspace member active status")
    role:WorkspaceRole=WorkspaceRole.MEMBER

class WorkspaceResponse(BaseSchema):
    id: str
    name: str
    owner_id: str
    created_at: datetime
    
class WorkspaceMemberResponse(BaseSchema):
    id: str
    user_id: str
    workspace_id: str
    role: WorkspaceRole
    joined_at: datetime    