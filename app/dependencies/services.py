from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.database import get_db
from app.services.auth import UserService
from app.repositories.auth import UserRepository
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