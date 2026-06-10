from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy import select
from app.repositories.workspace import WorkspaceRepository, WorkspaceMembers, Workspace
from app.config.config import get_settings
from app.schemas.workspace import WorkspaceRole
from app.models.auth import UserModel
from app.repositories.auth import UserRepository
from app.dependencies.pagination_cls import PaginationParams,PaginatedResponse

settings = get_settings()

class WorkspaceService :
  
   def __init__(self, db:AsyncSession):
        self.db = db
        self.repo = WorkspaceRepository(db) 

   async def create_workspace(self, user_id:str, workspace_data) -> None:
      try:
         # Check workspace_name empty
         if not workspace_data.name.strip():
            raise ValueError("Workspace name cannot be empty")
      
         if not ( 3 <= len(workspace_data.name) <= 100 ):
            raise ValueError("Workspace name should be minimum 3 and maximum 100 characters")
      
         # check duplicate workspace name
         is_exist =await self.repo.duplicate_workspace_name(user_id, workspace_data.name)
 
         if is_exist :
           raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="You already have a workspace with this name"
         )
     
         # Create workspace (includes member creation)
         new_workspace = await  self.repo.create_workspace(owner_id=user_id,workspace=workspace_data)
         print(f'Data : ${new_workspace}')
         return {
            "success": True,
            "message": "Workspace created successfully",
            "data": {
                "workspace_id": new_workspace.id,
                "workspace_name": new_workspace.name,
               #  "role": new_workspace.,
                "created_at": new_workspace.created_at.isoformat() if new_workspace.created_at else None
            }
        }
      
      except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
      except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace: {str(e)}"
        )
     
   async def get_workspace_by_id(self, workspace_id: str):
        
        workspace = await self.repo.get_workspace_by_id(workspace_id)

        if not workspace:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found"
            )

        return workspace
   
   async def get_user_role(self, workspace_id: str, user_id: str):
        role = await self.repo.get_user_role(workspace_id, user_id)

        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found for this user in workspace"
            )

        return role
   
   async def is_workspace_member(self, workspace_id: str, user_id: str):
        return await self.repo.is_workspace_member(workspace_id, user_id)
   
   async def update_workspace(self, workspace_id:str, data, user_id:str):

      workspace = await self.repo.get_workspace_by_id(workspace_id)

      if not workspace:
         raise HTTPException(404, "Workspace not found")
      
      existing = await self.repo.duplicate_workspace_name(user_id, data.name)
      if existing:
        raise HTTPException(400, "Workspace name already exists")

      # Partial update
      if data.name is not None:
         workspace.name = data.name.strip()

      if data.description is not None:
        workspace.description = data.description

      await self.db.commit()
      await self.db.refresh(workspace)

      return workspace
   
#     check memeber exist in db or not
   async def get_user_by_email(self, email: str):
      
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

   async def add_member_to_workspace(
    self,
    workspace_id: str,
    member_email: str,
    role: WorkspaceRole,
    current_user_id: str
):
    workspace = await self.get_workspace_by_id(workspace_id)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    current_user_role = await self.get_user_role(
        workspace_id,
        current_user_id
    )

    if current_user_role != WorkspaceRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace admin can add members"
        )

    user_to_add = await self.get_user_by_email(
        member_email
    )

    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{member_email}' not found"
        )

    existing_member = await self.is_workspace_member(
        workspace_id,
        user_to_add.id
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{member_email}' is already a member"
        )

    member = await self.repo.add_workspace_member(
        user_id=user_to_add.id,
        workspace_id=workspace_id,
        role=role
    )

    return {
        "workspace_id": workspace_id,
        "workspace_name": workspace.name,
        "user_id": user_to_add.id,
        "email": user_to_add.email,
        "name": user_to_add.user_name,
        "role": role.value,
        "joined_at": member.joined_at,
        "is_active": member.is_active,
        "message": f"User '{member_email}' added as {role.value} successfully"
    }
   
   async def get_user_workspaces(self, user_id: str,pagination: PaginationParams)-> dict:
 
    # Get total count
    count_stmt = (
        select(func.count())
        .select_from(Workspace)
        .join(WorkspaceMembers, Workspace.id == WorkspaceMembers.workspace_id)
        .where(
            WorkspaceMembers.user_id == user_id,
            WorkspaceMembers.is_active == True,
            Workspace.is_active == True
        )
    )
    total_count = await self.db.scalar(count_stmt)
    
    # Get paginated data
    stmt = (
        select(Workspace, WorkspaceMembers.role)
        .join(WorkspaceMembers, Workspace.id == WorkspaceMembers.workspace_id)
        .where(
            WorkspaceMembers.user_id == user_id,
            WorkspaceMembers.is_active == True,
            Workspace.is_active == True
        )
        .offset(pagination.skip)
        .limit(pagination.limit)
        .order_by(Workspace.created_at.desc())
    )
    
    result = await self.db.execute(stmt)
    workspaces = result.all()
    
    # Format response
    data = [
        {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "description": workspace.description,
            "role": role,
            "created_at": workspace.created_at.isoformat()
        }
        for workspace, role in workspaces
    ]
    
    return PaginatedResponse.create(data, total_count, pagination).dict()
