from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace, WorkspaceMembers, WorkspaceRole
from app.schemas.workspace import WorkspaceSchema
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timezone
import uuid
from sqlalchemy.sql import func

class WorkspaceRepository:
    "workspace repo for create, add member and get user workspace"

    def __init__(self, db:AsyncSession):
        self.db = db

    async def create_workspace(self, owner_id: str, workspace: WorkspaceSchema) -> Workspace:
        """Create workspace and add owner as ADMIN in ONE transaction"""
        
        try:
            # Create workspace
            current_time = datetime.now(timezone.utc)
            
            workspace_obj = Workspace(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                name=workspace.name.strip(),
                description=workspace.description,
                created_at=current_time,
                updated_at=current_time,
                is_active=True
            )
            
            self.db.add(workspace_obj)
            
            # Flush to get workspace.id (no commit)
            await self.db.flush()
            
            #  Create workspace member (owner as ADMIN)
            member = WorkspaceMembers(
                id=str(uuid.uuid4()),
                workspace_id=workspace_obj.id,
                user_id=owner_id,
                role=WorkspaceRole.ADMIN,
                joined_at=current_time,
                # invited_by=owner_id,  # Add who invited
                is_active=True
            )
            
            self.db.add(member)
            
            await self.db.commit()
        
            # Refresh workspace to get updated data
            await self.db.refresh(workspace_obj)
        
            return workspace_obj
           
            
        except IntegrityError as e:
            # Rollback handled by FastAPI automatically
            # if "workspaces_name_key" in str(e) or "duplicate" in str(e).lower():
            #     raise ValueError("Workspace name already exists")
            if "uq_owner_workspace_name" in str(e.orig) or "uq_user_workspace" in str(e.orig):
                raise ValueError("Workspace name already exists")
           
        
        except Exception as e:
            # Let FastAPI handle rollback
            raise e

    async def get_workspace_by_id(self, workspace_id: str) -> Workspace:
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def is_workspace_member(self, workspace_id: str, user_id: str) -> bool:
       try:
            result = await self.db.execute(
            select(WorkspaceMembers).where(
                WorkspaceMembers.workspace_id == workspace_id,
                WorkspaceMembers.user_id == user_id,
                WorkspaceMembers.is_active == True
            )
        )
            # return result.scalar_one_or_none() is not None
            return result.scalar()
       
       except Exception as e:
            # Log the error
            # logger.error(f"Failed to check workspace membership: {e}")
            print(f"Failed to check workspace membership: {e}")
            return False

    async def  get_user_role(self, workspace_id: str, user_id: str):
        result = await self.db.execute(
            select(WorkspaceMembers.role).where(
            WorkspaceMembers.workspace_id == workspace_id,
            WorkspaceMembers.user_id == user_id,
            WorkspaceMembers.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def add_workspace_member(
        self,
        user_id: str,
        workspace_id: str,
        role
    ):
        member = WorkspaceMembers(
            id=str(uuid.uuid4()),
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            is_active=True,
            joined_at=func.now()
        )

        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def remove_member():
        pass

    async def update_workspace() :
        pass

    async def delete_workspace() :
        pass

    async def duplicate_workspace_name(self, owner_id:str, workspace_name:str): 

            query = select(Workspace).where(Workspace.owner_id == owner_id,
            Workspace.name == workspace_name)
        
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        
    async def get_user_workspaces(self, user_id: str):

        stmt = (
            select(Workspace, WorkspaceMembers.role)
            .join(
                WorkspaceMembers,
                Workspace.id == WorkspaceMembers.workspace_id
            )
            .where(
                WorkspaceMembers.user_id == user_id,
                WorkspaceMembers.is_active == True,
                Workspace.is_active == True
            )
        )

        result = await self.db.execute(stmt)

        return result.all()
  
            
 
"""
 # create workspace
get_workspace_by_id()    # fetch one workspace
get_user_workspaces()    # all workspaces of logged in user
add_member()             # member add 
remove_member()          # member remove
update_workspace()       # workspace update 
delete_workspace()   

"""