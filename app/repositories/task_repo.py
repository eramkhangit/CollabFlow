from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskPriority


class TaskRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.is_deleted.is_(False),
            )
        )

        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:

        filters = [
            Task.project_id == project_id,
            Task.is_deleted.is_(False),
        ]

        if status:
            filters.append(Task.status == status)

        if priority:
            filters.append(Task.priority == priority)

        if assignee_id:
            filters.append(Task.assignee_id == assignee_id)

        # Count total records
        count_result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(*filters)
        )

        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Task)
            .where(*filters)
            .order_by(
                case(
                    (Task.due_date.is_(None), 1),
                    else_=0,
                ),
                Task.due_date.asc(),
                Task.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = result.scalars().all()

        return items, total

    async def create(self, task: Task) -> Task:
        self.db.add(task)

        await self.db.flush()

        # Load generated DB values
        await self.db.refresh(task)

        return task

    async def update(
        self,
        task: Task,
        data: dict,
    ) -> Task:

        for key, value in data.items():
            setattr(task, key, value)

        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def soft_delete(self, task: Task) -> None:

        task.is_deleted = True
        task.deleted_at = datetime.now(timezone.utc)

        await self.db.flush()