from sqlalchemy.orm import Session
from app.models.workspace import Workspace, WorkspaceMembers
from typing import Optional,List, Tuple,Union
from sqlalchemy.exc import IntegrityError

class WorkspaceRepository:
    "workspace repo for create, add member and get user workspace"

    def __init__(self, db:Session):
        self.db = db

    def create_workspace(self,):
        pass

"""
create_workspace()
add_member()
get_user_workspaces()
get_workspace_by_id()
check_user_role() 
"""