# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import datetime
# from app.models.project import ProjectStatus


# class ProjectCreate(BaseModel):
#     name: str = Field(..., min_length=1, max_length=200)
#     description: Optional[str] = None
#     status: ProjectStatus = ProjectStatus.active
#     due_date: Optional[datetime] = None
#     # member_ids: Optional[list[str]] = None  #  attach members on create


# class ProjectOut(BaseModel):
#     id: str
#     name: str
#     status: ProjectStatus
#     description: Optional[str] = None
#     owned_by: str
#     created_at: datetime
#     updated_at: datetime
#     completed_at: Optional[datetime] = None
#     due_date: Optional[datetime] = None

#     class Config:
#         from_attributes = True  


from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus


# ---------- Request schemas ----------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.active
    due_date: Optional[datetime] = None
    member_ids: Optional[List[str]] = None


class ProjectUpdate(BaseModel):
    """All fields optional — PATCH semantics (partial update)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    member_ids: Optional[List[str]] = None


# ---------- Response schemas ----------

class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_name: str
    email: str


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    name: str
    status: ProjectStatus
    description: Optional[str] = None
    owned_by: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None


class ProjectStats(BaseModel):
    total_tickets: int = 0
    open_tickets: int = 0
    completed_tickets: int = 0
    member_count: int = 0


class ProjectDetailOut(ProjectOut):
    owner: UserBrief
    members: List[UserBrief] = []
    stats: ProjectStats


class ProjectOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class PaginatedProjects(BaseModel):
    items: List[ProjectOut]
    total: int
    page: int
    page_size: int
    total_pages: int