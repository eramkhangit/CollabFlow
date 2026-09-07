from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.core.security import decode_token 
from app.core.database import get_db
from app.models.auth import UserModel
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import UserService

logger = logging.getLogger(__name__)

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    """
    Get current authenticated user from JWT token.
    
    Security:
    - Extracts token from Authorization header
    - Validates Bearer scheme
    - Decodes and validates JWT
    - Fetches user from database
    - Checks if user exists
    """
    
    # Extract token 
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        logger.warning("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate Bearer scheme
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            logger.warning(f"Invalid authentication scheme: {scheme}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )
       
    except ValueError:
        logger.warning("Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode JWT token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            logger.warning("Token missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing 'sub' field",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        logger.debug(f"User authenticated: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error authenticating user",
        )


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user) 
) -> UserModel:
    """
    Get current active user - extends get_current_user with active checks.
    
    Checks:
    - User is active (is_active = True)
    - Email is verified (optional)
    """
    
    # Check if user is active
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user. Please contact support.",
        )
    
    # Email verification check
    if hasattr(current_user, 'is_verified') and not current_user.is_verified:
        logger.warning(f"Unverified email: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email.",
        )
    
    return current_user


async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Get current admin user - requires admin role.
    """
    if current_user.role != "admin":
        logger.warning(f"Non-admin user attempted admin access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_workspace_member(
    workspace_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    """
    Verify user is a member of the workspace.
    """
    
    member_repo = WorkspaceRepository(db)
    is_member = await member_repo.check_membership(workspace_id, current_user.id)
    
    if not is_member:
        logger.warning(f"User {current_user.id} not member of workspace {workspace_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )
    
    return current_user