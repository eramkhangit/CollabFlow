from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import get_current_workspace_membership
from app.models.auth import UserModel
from app.models.project import ProjectStatus
from app.models.workspace import WorkspaceMembers
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectDetailOut,
    ProjectOption,
    PaginatedProjects,
    ProjectStats,
)
from app.services.project_service import ProjectService


# All project APIs are scoped to a workspace.
# The workspace_id is taken from the URL and validated through
# get_current_workspace_membership before the endpoint is executed.
router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
)


def get_project_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectService:
    """
    Dependency that creates a ProjectService using the current
    database session.

    Keeping service creation here allows the route handlers to focus
    only on HTTP concerns while business logic remains inside
    ProjectService.
    """
    return ProjectService(db)


@router.get("/options", response_model=list[ProjectOption])
async def get_project_options(
    search: Optional[str] = Query(None),
    membership: WorkspaceMembers = Depends(get_current_workspace_membership),
    service: ProjectService = Depends(get_project_service),
):
    """
    Return lightweight project options for UI components such as
    dropdowns and autocomplete/search fields.

    Only projects belonging to the current workspace are returned.
    """
    return await service.list_options(
        membership.workspace_id,
        search,
    )


@router.get("", response_model=PaginatedProjects)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ProjectStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    owned_by: Optional[str] = Query(None),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|updated_at|name|due_date)$",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
    ),
    membership: WorkspaceMembers = Depends(get_current_workspace_membership),
    service: ProjectService = Depends(get_project_service),
):
    """
    Return a paginated list of projects for the current workspace.

    Supported filters:
    - status: Filter projects by project status.
    - search: Search projects by the supported searchable fields.
    - owned_by: Filter projects by owner.
    - sort_by: Sort by created_at, updated_at, name, or due_date.
    - sort_order: Sort ascending or descending.

    Pagination values are validated by FastAPI before reaching
    the service layer.
    """
    return await service.list_projects(
        membership.workspace_id,
        page,
        page_size,
        status_filter,
        search,
        owned_by,
        sort_by,
        sort_order,
    )


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: str,
    membership: WorkspaceMembers = Depends(get_current_workspace_membership),
    service: ProjectService = Depends(get_project_service),
):
    """
    Return detailed information about a single project.

    The service returns the project together with its calculated
    statistics. The route then maps these values into the
    ProjectDetailOut response schema.
    """
    result = await service.get_project_detail(
        project_id,
        membership.workspace_id,
    )

    project = result["project"]

    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        owner=project.owner,
        members=project.members,
        stats=ProjectStats(**result["stats"]),
    )


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: ProjectCreate,
    current_user: UserModel = Depends(get_current_user),
    membership: WorkspaceMembers = Depends(get_current_workspace_membership),
    service: ProjectService = Depends(get_project_service),
):
    """
    Create a new project inside the current workspace.

    current_user is used to identify the user performing the action,
    while membership provides the workspace context and verifies that
    the user belongs to that workspace.
    """
    return await service.create_project(
        payload,
        membership.workspace_id,
        current_user,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: UserModel = Depends(get_current_user),
    membership: WorkspaceMembers = Depends(get_current_workspace_membership),
    service: ProjectService = Depends(get_project_service),
):
    """
    Update an existing project.

    The service layer is responsible for validating the project,
    applying the requested changes, and enforcing update permissions.
    The workspace membership is passed so the service can also perform
    role/permission checks where required.
    """
    return await service.update_project(
        project_id,
        payload,
        membership.workspace_id,
        current_user,
        membership,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: str,
    current_user: UserModel = Depends(get_current_user),
    membership: WorkspaceMembers = Depends(get_current_workspace_membership),
    service: ProjectService = Depends(get_project_service),
):
    """
    Delete a project from the current workspace.

    The service layer performs the actual deletion and permission
    validation. A successful DELETE returns HTTP 204 with no response body.
    """
    await service.delete_project(
        project_id,
        membership.workspace_id,
        current_user,
        membership,
    )

    return None