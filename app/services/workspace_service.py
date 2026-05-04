from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError 
from datetime import datetime, timezone,timedelta
import uuid
from app.repositories.workspace import WorkspaceRepository
from app.config.config import get_settings


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
         new_workspace = await  self.repo.create_workspace(owner_id=user_id,    workspace=workspace_data)

         return {
            "success": True,
            "message": "Workspace created successfully",
            "data": {
                "workspace_id": new_workspace.id,
                "workspace_name": new_workspace.name,
                "role": "ADMIN",
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
     

   
#   getWorkspaceById() { }
#   updateWorkspace() { }
#   deleteWorkspace() { }
