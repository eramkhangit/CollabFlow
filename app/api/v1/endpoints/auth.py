from fastapi import APIRouter, Request, Response
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status,Depends, HTTPException
from app.schemas.auth import UserResponse, User,LoginResponse,LoginRequest
from app.services.auth import UserService
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_auth_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/user', tags=['user'])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account "
    )
async def register(user_data:User, service: UserService = Depends(get_auth_service))->UserResponse :
    """register a user"""
    try:

        user=await service.create_user(user_data)

        if user is None:
            # logger.error("User creation returned None")
            print("User creation returned None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed"
            )
 
        return user
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login a user",
    description="Login a user"
    )
async def login(login_data:LoginRequest,
        request: Request ,
        response: Response,
        service: UserService = Depends(get_auth_service)) -> LoginResponse :
    try:
        user=await service.login_user(login_data, request=request,response=response)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return user
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post(
    "/refresh-token",
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate a new access token using the refresh token stored in the HttpOnly cookie"
)
async def refresh(
    request: Request,
    response: Response,
    service: UserService = Depends(get_auth_service)
):
    try: 
        return await service.refresh_access_token(
            request=request,
            response=response
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Unexpected error during token refresh") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Please try again."
        )

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in user",
    description="Returns the profile of the currently authenticated user based on the access token"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_auth_service)
    # user_service: UserService = Depends(get_user_service) 
):
    """
    Logout user - revoke refresh token and clear cookie
    """
    # ✅ Get refresh token from cookie (NOT query parameter)
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token found"
        )
    
    # Revoke the token
    revoked = await service.revoke_refresh_token(refresh_token)
    
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already revoked token"
        )
    
    # Clear the cookie
    response.delete_cookie(
        key="refresh_token",
        # path="/api/v1/user/refresh-token"  # Match the path used when setting
        path="/"
    )
    
    return {"message": "Logged out successfully"}