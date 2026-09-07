# app/dependencies/services.py

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.database import get_db
from app.services.auth import UserService
# from app.services.user import UserService
# from app.services.workspace import WorkspaceService
from app.repositories.auth import UserRepository
# from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository

async def get_auth_service(
    db: AsyncSession = Depends(get_db)
) -> UserService:
    """Get UserService instance."""
    return UserService(db)

async def get_user_service(
    db: AsyncSession = Depends(get_db)
) -> UserService:
    """Get UserService instance."""
    return UserService(db)

# async def get_workspace_service(
#     db: AsyncSession = Depends(get_db)
# ) -> WorkspaceService:
#     """Get WorkspaceService instance."""
#     repo = WorkspaceRepository(db)
#     return WorkspaceService(repo)