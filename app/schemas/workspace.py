from pydantic import BaseModel, Field,ConfigDict
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
    is_active:bool=Field(...,default=True, description="Workspace active or not")

class WorkspaceMembersSchema(BaseSchema):
    user_id:str=Field(..., description="User id")
    workspace_id:str=Field(..., description="workspace id")
    is_active:bool=Field(...,default=True, description="Workspace member active status")
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