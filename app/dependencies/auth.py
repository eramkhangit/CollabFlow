from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.security import decode_token 
from app.core.database import get_db
from app.models.auth import UserModel
from app.services.auth import UserService


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> UserModel:
   
    #  Extract token from header 
    auth_header = request.headers.get("Authorization")
    print(f'Missing : ${auth_header}')
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    #  Validate Bearer scheme
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        print(f'Token : {token}')
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    #  Decode JWT token ---
    try:
        payload = decode_token(token)  # Throws exception if invalid
        print(f'Payload : ${payload}')
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing 'sub' field",
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    #  Fetch user from database
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user) 
) -> UserModel:

    
    #  Check if user is active 

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user. Please contact support.",
        )
    
    #Optional - Email verification check ---
    if hasattr(current_user, 'is_email_verified') and not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email.",
        )
    
    return current_user


async def get_workspace_member(
    workspace_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
   
    pass
    # Check if user is member of this workspace
    # from app.repositories.workspace_member import WorkspaceMemberRepository
    
    # member_repo = WorkspaceMemberRepository(db)
    # is_member = await member_repo.check_membership(workspace_id, current_user.id)
    
    # if not is_member:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You are not a member of this workspace",
    #     )
    
    # return current_user