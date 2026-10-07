from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.task import TaskStatus, TaskPriority
from app.repositories.task_repo import TaskRepository
from app.services.task import TaskService
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskRead,
    TaskListResponse,
)
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

def get_task_service(
    db: AsyncSession = Depends(get_db),
) -> TaskService:

    return TaskService(
        TaskRepository(db)
    )

@router.get(
    "",
    response_model=TaskListResponse,
)
async def list_tasks(
    project_id: str = Query(...),
    status_filter: Optional[TaskStatus] = Query(
        None,
        alias="status",
    ),
    priority: Optional[TaskPriority] = Query(None),
    assignee_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    service: TaskService = Depends(get_task_service),
):

    items, total = await service.list_tasks(
        project_id,
        status_filter,
        priority,
        assignee_id,
        page,
        page_size,
    )

    return TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )

@router.get(
    "/{task_id}",
    response_model=TaskRead,
)
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
):

    try:
        return await service.get_task(task_id)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    data: TaskCreate,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):

    current_user_id = current_user.id
    task = await service.create_task(
        data,
        created_by_id=current_user_id,
    )

    await service.repository.db.commit()

    return task

@router.patch(
    "/{task_id}",
    response_model=TaskRead,
)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):

    try:
        task = await service.update_task(
            task_id,
            data,
        )

        await service.repository.db.commit()

        return task

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
# soft delete  
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
):

    try:
        await service.delete_task(task_id)

        await service.repository.db.commit()

        return None

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )