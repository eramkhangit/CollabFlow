from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status,Depends, HTTPException
from app.schemas.workspace import WorkspaceSchema
from app.services.workspace_service import WorkspaceService
from app.models.auth import UserModel

router = APIRouter(prefix='/workspace', tags=['workspace'])

@router.post(
   "/create-workspace",
    status_code=status.HTTP_201_CREATED,
    summary="create a new workspace",
    description="Create a new workspace"
)
async def create_workspace(workspace_data:WorkspaceSchema, 
    current_user: UserModel = Depends(get_current_user),
    db:AsyncSession=Depends(get_db)):
    """create a workspace"""
    try:
       service = WorkspaceService(db)
       created_workspace = await service.create_workspace(current_user.id,workspace_data)

       return created_workspace 
    
    except HTTPException as e :
        raise e
     