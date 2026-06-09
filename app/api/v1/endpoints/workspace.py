from fastapi import APIRouter, Depends,Query
from app.dependencies.auth import get_current_user
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status,Depends, HTTPException
from app.schemas.workspace import WorkspaceSchema,WorkspaceUpdateSchema, WorkspaceResponse,WorkspaceDetailResponse, AddMemberSchema,MemberResponse, WorkspaceCreateResponse,WorkspaceListResponse
from app.services.workspace_service import WorkspaceService
from app.models.auth import UserModel
from app.models.workspace import WorkspaceRole
from uuid import UUID
from app.dependencies.pagination_cls import PaginationParams

router = APIRouter(prefix='/workspace', tags=['workspace'])

@router.post(
   "/create-workspace",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkspaceCreateResponse,
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
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e
     
@router.get(
   "/workspace-details/{workspace_id}",
    status_code=status.HTTP_200_OK,
    response_model=WorkspaceDetailResponse,
    summary="Get a workspace details", 
    description="Get a workspace details"
)
async def workspace_details(workspace_id:str, 
    current_user: UserModel = Depends(get_current_user),
    db:AsyncSession=Depends(get_db)):
        """get specific workspace details"""

        service = WorkspaceService(db)
        
        is_member = await service.is_workspace_member(workspace_id,user_id=current_user.id)

        if not is_member:
           raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
           )
    
        workspace = await service.get_workspace_by_id(workspace_id)

        role = await service.get_user_role(workspace_id, current_user.id)

        return WorkspaceDetailResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        owner_name=workspace.owner.user_name, 
        is_active=workspace.is_active,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        my_role=role 
    )

@router.patch(
   "/update-workspace/{workspace_id}",
    status_code=status.HTTP_200_OK,
    response_model=WorkspaceResponse,
    summary="Update workspace", 
    description="Update workspace"
)
async def update_workspace(workspace_id:str, 
    data:WorkspaceUpdateSchema,
    current_user: UserModel = Depends(get_current_user),
    db:AsyncSession=Depends(get_db)):
    """Update workspace"""

    service = WorkspaceService(db)
    role = await service.get_user_role(workspace_id,current_user.id)
    
    if role != WorkspaceRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace admin can update workspace"
           )
    
    updated_workspace = await service.update_workspace(
        workspace_id,
        data,
        current_user.id
    )

    return updated_workspace

@router.post(
   "/add-member/{workspace_id}",
    status_code=status.HTTP_200_OK,
    response_model=MemberResponse,
    summary="Add a member to workspace", 
    description="Add a new member to workspace (Only workspace admin can do this)"
)
async def add_member(
    workspace_id:str,  
    member_data: AddMemberSchema,
    current_user: UserModel = Depends(get_current_user),
    db:AsyncSession=Depends(get_db)) :
    service = WorkspaceService(db)

    try:
        result = await service.add_member_to_workspace(
            workspace_id=workspace_id,
            member_email=member_data.member_email,
            role=member_data.role,
            current_user_id=current_user.id
        )
        
        return  MemberResponse(
            workspace_id=result["workspace_id"],
            # workspace_name=result["workspace_name"],
            user_id=result["user_id"],
            email=result["email"],
            # user_name=result["user_name"],
            role=result["role"],
            joined_at=result["joined_at"],
            is_active=result["is_active"],
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}"
        )
    
@router.get('/get-user-workspaces/{user_id}',
        status_code=status.HTTP_200_OK,
        # response_model=
        summary="Get a user's all workspaces", 
        description="Get all workspaces of a user"
        ) 
   
async def get_all_workspaces(
    user_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db:AsyncSession=Depends(get_db)) -> WorkspaceListResponse :
    workspace_service = WorkspaceService(db)
    
    # Prevent users from viewing other users' workspaces
    user_id_str = str(user_id)
    current_user_id_str = str(current_user.id)
    
    print(f'User : {current_user_id_str} and {user_id_str}')
    
    if user_id_str != current_user_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own workspaces"
        )
    print (f'Errr : ${user_id}')
    # Create pagination params
    pagination_params = PaginationParams(page=page, page_size=page_size)
    
    workspace_service = WorkspaceService(db)
    return await workspace_service.get_user_workspaces(
        current_user.id,
        pagination_params
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a workspace (soft delete) - Only workspace owners or admins can delete """
    workspace_service = WorkspaceService(db)
    
    # Check if workspace exists and user has permission
    workspace = await workspace_service.get_workspace_by_id(workspace_id)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check user's role in this workspace
    user_role = await workspace_service.get_user_role_in_workspace(
        workspace_id, 
        current_user.id
    )
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Only allow owner or admin to delete
    if user_role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or admins can delete workspaces"
        )
    
    #  soft delete
    await workspace_service.delete_workspace(workspace_id, current_user.id)
    
    return None