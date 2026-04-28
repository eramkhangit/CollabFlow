from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace, WorkspaceMembers
from app.schemas.workspace import WorkspaceSchema
from typing import Optional,List, Tuple,Union
from sqlalchemy.exc import IntegrityError

class WorkspaceRepository:
    "workspace repo for create, add member and get user workspace"

    def __init__(self, db:AsyncSession):
        self.db = db

    async def create_workspace(self,owner_id:str,workspace:WorkspaceSchema) -> Workspace:

        """Create workspace and add owner as ADMIN in ONE transaction"""
        workspace = workspace(

        )


"""
 # create workspace
get_workspace_by_id()    # fetch one workspace
get_user_workspaces()    # all user's workspaces
add_member()             # member add 
remove_member()          # member remove
update_workspace()       # workspace update 
delete_workspace()   
"""