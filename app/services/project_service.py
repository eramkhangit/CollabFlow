from typing import Optional, List
from math import ceil
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.auth import UserModel
from app.models.workspace import WorkspaceMembers, WorkspaceRole
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    async def list_projects(
        self, workspace_id: str, page: int, page_size: int,
        status_filter: Optional[ProjectStatus], search: Optional[str],
        owned_by: Optional[str], sort_by: str, sort_order: str,
    ):
        items, total = await self.repo.list_paginated(
            workspace_id, page, page_size, status_filter, search, owned_by, sort_by, sort_order
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if page_size else 0,
        }

    async def list_options(self, workspace_id: str, search: Optional[str]) -> List[Project]:
        return await self.repo.list_options(workspace_id, search)

    async def get_project_detail(self, project_id: str, workspace_id: str) -> dict:
        project = await self.repo.get_by_id(project_id, workspace_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        stats = await self.repo.get_stats(project_id)
        stats["member_count"] = len(project.members)
        return {"project": project, "stats": stats}

    async def create_project(self, payload: ProjectCreate, workspace_id: str, current_user: UserModel) -> Project:
        if await self.repo.name_exists(payload.name, workspace_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A project with this name already exists in this workspace",
            )

        project = Project(
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            due_date=payload.due_date,
            owned_by=current_user.id,
        )

        if payload.member_ids:
            members = await self.repo.get_users_by_ids(payload.member_ids, workspace_id)
            if len(members) != len(set(payload.member_ids)):
                raise HTTPException(status_code=400, detail="One or more member_ids are invalid workspace members")
            project.members = members

        return await self.repo.create(project)

    async def update_project(
        self, project_id: str, payload: ProjectUpdate, workspace_id: str,
        current_user: UserModel, membership: WorkspaceMembers
    ) -> Project:
        project = await self.repo.get_by_id(project_id, workspace_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        self._assert_can_modify(project, current_user, membership)

        data = payload.model_dump(exclude_unset=True, exclude={"member_ids"})

        if "name" in data and data["name"] != project.name:
            if await self.repo.name_exists(data["name"], workspace_id, exclude_id=project_id):
                raise HTTPException(status_code=409, detail="A project with this name already exists")

        for field, value in data.items():
            setattr(project, field, value)

        if payload.member_ids is not None:
            members = await self.repo.get_users_by_ids(payload.member_ids, workspace_id)
            if len(members) != len(set(payload.member_ids)):
                raise HTTPException(status_code=400, detail="One or more member_ids are invalid workspace members")
            project.members = members

        return await self.repo.update(project)

    async def delete_project(self, project_id: str, workspace_id: str, current_user: UserModel, membership: WorkspaceMembers) -> None:
        project = await self.repo.get_by_id(project_id, workspace_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        self._assert_can_modify(project, current_user, membership)
        await self.repo.delete(project)

    def _assert_can_modify(self, project: Project, current_user: UserModel, membership: WorkspaceMembers) -> None:
        is_owner = project.owned_by == current_user.id
        is_workspace_admin = membership.role == WorkspaceRole.ADMIN
        if not (is_owner or is_workspace_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this project",
            )