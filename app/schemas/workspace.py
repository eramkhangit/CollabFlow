from pydantic import BaseModel, Field,ConfigDict, field_validator
from typing import Optional,List
from app.models.workspace import WorkspaceRole
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class WorkspaceSchema(BaseSchema):
    # owner_id:str=Field(..., description="Owner id")
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

class WorkspaceUpdateSchema(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name")
    def validate_name(cls, value):
        if value and not (3 <= len(value.strip()) <= 100):
            raise ValueError("Name must be between 3 and 100 characters")
        return value.strip() if value else value

# class WorkspaceMembersSchema(BaseSchema):
#     user_id:str=Field(..., description="User id")
#     workspace_id:str=Field(..., description="workspace id")
#     is_active:bool=Field(default=True, description="Workspace member active status")
#     role:WorkspaceRole=WorkspaceRole.MEMBER

class WorkspaceResponse(BaseSchema):
    id: str
    name: str
    owner_id: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] 

class WorkspaceDetailResponse(BaseSchema):
    id: str
    name: str
    owner_id: str
    owner_name: str              
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    my_role: Optional[WorkspaceRole] = None       

class AddMemberSchema(BaseSchema):
    member_email: str = Field(..., description="Email of user to add")
    role: WorkspaceRole = Field(default=WorkspaceRole.MEMBER, description="Role to assign")

class MemberResponse(BaseSchema):
    workspace_id: str
    user_id: str
    email: str
    # user_name: Optional[str]
    # workspace_name=Optional[str]
    role: WorkspaceRole
    joined_at: datetime
    is_active: bool

# create workspace response 
class WorkspaceData(BaseModel):
    workspace_id: str
    workspace_name: str
    created_at: datetime

class WorkspaceCreateResponse(BaseModel):
    success: bool
    message: str
    data: WorkspaceData

# workspace list response 
class WorkspaceItem(BaseModel):
    workspace_id: str
    workspace_name: str
    role: str

class WorkspaceListResponse(BaseModel):
    success: bool
    data: List[WorkspaceItem]    