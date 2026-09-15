from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.auth import UserModel
from app.models.workspace import WorkspaceMembers


async def get_current_workspace_membership(
    workspace_id: str = Path(..., description="Workspace ID from the URL path"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMembers:
    """
    Verifies current_user is an active member of workspace_id.
    Returns the membership row (includes .role for permission checks downstream).
    Raises 403 if not a member — NOT 404, so we don't leak whether the workspace exists.
    """

    result = await db.execute(
        select(WorkspaceMembers).where(
            WorkspaceMembers.workspace_id == workspace_id,
            WorkspaceMembers.user_id == current_user.id,
            WorkspaceMembers.is_active.is_(True),
        )
    )

    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )

    return membership