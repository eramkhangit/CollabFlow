from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace, WorkspaceMembers
from app.schemas.workspace import WorkspaceSchema
from typing import Optional,List, Tuple,Union
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

class WorkspaceRepository:
    "workspace repo for create, add member and get user workspace"

    def __init__(self, db:AsyncSession):
        self.db = db

    async def create_workspace(self, owner_id: str, workspace: WorkspaceSchema) -> Workspace:
        """Create workspace and add owner as ADMIN in ONE transaction"""
        
        try:
            # 1. Create workspace
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
                role="ADMIN",
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
            if "workspaces_name_key" in str(e) or "duplicate" in str(e).lower():
                raise ValueError("Workspace name already exists")
            raise e
        
        except Exception as e:
            # Let FastAPI handle rollback
            raise e


    async def get_workspace_by_id() : 
        pass

    async def get_user_workspaces() :
        pass

    async def add_member() :
        pass

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
        
        
            
 
"""
 # create workspace
get_workspace_by_id()    # fetch one workspace
get_user_workspaces()    # all user's workspaces
add_member()             # member add 
remove_member()          # member remove
update_workspace()       # workspace update 
delete_workspace()   



from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace, WorkspaceMembers
from app.schemas.workspace import WorkspaceSchema
from typing import Optional, List, Tuple, Union
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

class WorkspaceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workspace(self, owner_id: str, workspace: WorkspaceSchema) -> Workspace:
        # Create workspace and add owner as ADMIN in ONE transaction
        
        # ❌ REMOVE async with self.db.begin() - FastAPI already has transaction
        
        try:
            # 1. Create workspace
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
            
            # 2. Create workspace member (owner as ADMIN)
            member = WorkspaceMembers(
                id=str(uuid.uuid4()),
                workspace_id=workspace_obj.id,
                user_id=owner_id,
                role="ADMIN",
                joined_at=current_time,
                invited_by=owner_id,  # Add who invited
                is_active=True
            )
            
            self.db.add(member)
            
            # 3. Let FastAPI handle commit automatically
            # DON'T call commit() here
            
            # Refresh workspace to get updated data
            await self.db.refresh(workspace_obj)
            
            return workspace_obj
            
        except IntegrityError as e:
            # Rollback handled by FastAPI automatically
            if "workspaces_name_key" in str(e) or "duplicate" in str(e).lower():
                raise ValueError("Workspace name already exists")
            raise e
        
        except Exception as e:
            # Let FastAPI handle rollback
            raise e


    async def get_workspace_by_id(self, workspace_id: str, user_id: str = None):
        Get workspace by ID, optionally check user membership
        
        query = select(Workspace).where(Workspace.id == workspace_id)
        
        if user_id:
            # Check if user has access to this workspace
            query = query.where(Workspace.owner_id == user_id)
        
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()


    async def get_user_workspaces(self, user_id: str, skip: int = 0, limit: int = 10):
        Get all workspaces where user is a member
        
        # Join workspaces with workspace_membership
        query = select(Workspace).join(
            WorkspaceMembers, 
            Workspace.id == WorkspaceMembers.workspace_id
        ).where(
            WorkspaceMembers.user_id == user_id,
            Workspace.is_active == True
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.unique().scalars().all()


    async def add_member(self, workspace_id: str, user_id: str, invited_by: str, role: str = "MEMBER"):
     
        
        # Check if member already exists
        existing = await self.get_member(workspace_id, user_id)
        if existing:
            raise ValueError("User is already a member of this workspace")
        
        current_time = datetime.now(timezone.utc)
        
        member = WorkspaceMembers(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            joined_at=current_time,
            invited_by=invited_by,
            is_active=True
        )
        
        self.db.add(member)
        await self.db.flush()
        
        return member


    async def remove_member(self, workspace_id: str, user_id: str):
    
        
        # Get member record
        query = select(WorkspaceMembers).where(
            WorkspaceMembers.workspace_id == workspace_id,
            WorkspaceMembers.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise ValueError("Member not found")
        
        # Check if this is the last ADMIN
        if member.role == "ADMIN":
            admin_count = await self.count_admins(workspace_id)
            if admin_count <= 1:
                raise ValueError("Cannot remove last ADMIN of workspace")
        
        # Soft delete
        member.is_active = False
        await self.db.flush()
        
        return True


    async def update_workspace(self, workspace_id: str, user_id: str, **kwargs):

        
        # Check if user is ADMIN
        is_admin = await self.check_admin_role(workspace_id, user_id)
        if not is_admin:
            raise PermissionError("Only ADMIN can update workspace")
        
        # Get workspace
        query = select(Workspace).where(Workspace.id == workspace_id)
        result = await self.db.execute(query)
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Update allowed fields
        allowed_fields = ["name", "description", "is_active", "settings"]
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(workspace, key, value)
        
        # Update timestamp
        workspace.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        await self.db.refresh(workspace)
        
        return workspace


    async def delete_workspace(self, workspace_id: str, user_id: str):
       
        
        # Check if user is ADMIN
        is_admin = await self.check_admin_role(workspace_id, user_id)
        if not is_admin:
            raise PermissionError("Only ADMIN can delete workspace")
        
        # Get workspace
        query = select(Workspace).where(Workspace.id == workspace_id)
        result = await self.db.execute(query)
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Soft delete
        workspace.is_active = False
        workspace.updated_at = datetime.now(timezone.utc)
        
        # Also soft delete all members
        query = select(WorkspaceMembers).where(WorkspaceMembers.workspace_id == workspace_id)
        result = await self.db.execute(query)
        members = result.scalars().all()
        
        for member in members:
            member.is_active = False
        
        await self.db.flush()
        
        return True


    async def duplicate_workspace_name(self, owner_id: str, workspace_name: str):
        
        
        query = select(Workspace).where(
            Workspace.owner_id == owner_id,
            Workspace.name == workspace_name,
            Workspace.is_active == True
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


    # ========== Helper Methods ==========
    
    async def get_member(self, workspace_id: str, user_id: str):
        
        
        query = select(WorkspaceMembers).where(
            WorkspaceMembers.workspace_id == workspace_id,
            WorkspaceMembers.user_id == user_id,
            WorkspaceMembers.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


    async def check_admin_role(self, workspace_id: str, user_id: str) -> bool:
      
        
        member = await self.get_member(workspace_id, user_id)
        return member is not None and member.role == "ADMIN"


    async def count_admins(self, workspace_id: str) -> int:
     
        
        query = select(WorkspaceMembers).where(
            WorkspaceMembers.workspace_id == workspace_id,
            WorkspaceMembers.role == "ADMIN",
            WorkspaceMembers.is_active == True
        )
        result = await self.db.execute(query)
        admins = result.scalars().all()
        return len(admins)


    async def get_user_role(self, workspace_id: str, user_id: str) -> Optional[str]:

        
        # member = await self.get_member(workspace_id, user_id)
        # return member.role if member else None



"""