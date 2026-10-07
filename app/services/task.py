from typing import Optional

from app.models.task import Task, TaskStatus, TaskPriority
from app.repositories.task_repo import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.exceptions import NotFoundError


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    async def get_task(self, task_id: str) -> Task:
        task = await self.repository.get_by_id(task_id)

        if not task:
            raise NotFoundError(f"Task {task_id} not found")

        return task

    async def list_tasks(
        self,
        project_id: str,
        status: Optional[TaskStatus],
        priority: Optional[TaskPriority],
        assignee_id: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Task], int]:

        return await self.repository.list_by_project(
            project_id,
            status,
            priority,
            assignee_id,
            page,
            page_size,
        )

    async def create_task(
        self,
        data: TaskCreate,
        created_by_id: Optional[str],
    ) -> Task:

        task = Task(
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            assignee_id=data.assignee_id,
            labels=data.labels,
            project_id=data.project_id,
            created_by_id=created_by_id,
        )

        return await self.repository.create(task)

    async def update_task(
        self,
        task_id: str,
        data: TaskUpdate,
    ) -> Task:

        task = await self.get_task(task_id)

        update_data = data.model_dump(exclude_unset=True)

        return await self.repository.update(
            task,
            update_data,
        )

    async def delete_task(self, task_id: str) -> None:

        task = await self.get_task(task_id)

        await self.repository.soft_delete(task)