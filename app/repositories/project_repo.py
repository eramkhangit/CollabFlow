from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.project import Project, ProjectStatus
from app.models.auth import UserModel
from app.models.workspace import WorkspaceMembers
from app.models.ticket import Ticket, TicketStatus


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: str, workspace_id: str) -> Optional[Project]:
        stmt = (
            select(Project)
            .options(joinedload(Project.owner), joinedload(Project.members))
            .where(Project.id == project_id, Project.workspace_id == workspace_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_paginated(
        self,
        workspace_id: str,
        page: int,
        page_size: int,
        status: Optional[ProjectStatus] = None,
        search: Optional[str] = None,
        owned_by: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Project], int]:
        base_stmt = select(Project).where(Project.workspace_id == workspace_id)

        if status:
            base_stmt = base_stmt.where(Project.status == status)
        if owned_by:
            base_stmt = base_stmt.where(Project.owned_by == owned_by)
        if search:
            like = f"%{search}%"
            base_stmt = base_stmt.where(or_(Project.name.ilike(like), Project.description.ilike(like)))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        sort_column = getattr(Project, sort_by, Project.created_at)
        base_stmt = base_stmt.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        base_stmt = base_stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(base_stmt)
        items = result.scalars().all()
        return items, total

    async def list_options(self, workspace_id: str, search: Optional[str] = None, limit: int = 50) -> List[Project]:
        stmt = select(Project.id, Project.name).where(Project.workspace_id == workspace_id)
        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(Project.name.asc()).limit(limit)
        result = await self.db.execute(stmt)
        return result.all()

    async def get_stats(self, project_id: str) -> dict:
        total_stmt = select(func.count(Ticket.id)).where(Ticket.project_id == project_id)
        total_tickets = (await self.db.execute(total_stmt)).scalar_one() or 0

        open_stmt = select(func.count(Ticket.id)).where(
            Ticket.project_id == project_id, Ticket.status != TicketStatus.done
        )
        open_tickets = (await self.db.execute(open_stmt)).scalar_one() or 0

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "completed_tickets": total_tickets - open_tickets,
        }

    async def get_users_by_ids(self, user_ids: List[str], workspace_id: str) -> List[UserModel]:
        stmt = (
            select(UserModel)
            .join(WorkspaceMembers, WorkspaceMembers.user_id == UserModel.id)
            .where(
                UserModel.id.in_(user_ids),
                WorkspaceMembers.workspace_id == workspace_id,
                WorkspaceMembers.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def name_exists(self, name: str, workspace_id: str, exclude_id: Optional[str] = None) -> bool:
        stmt = select(Project.id).where(Project.workspace_id == workspace_id, Project.name == name)
        if exclude_id:
            stmt = stmt.where(Project.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.first() is not None

    async def create(self, project: Project) -> Project:
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.commit()