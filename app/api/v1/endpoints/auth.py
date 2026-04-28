from fastapi import APIRouter, Request
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status,Depends, HTTPException
from app.schemas.auth import UserResponse, User,LoginResponse,LoginRequest
from app.services.auth import UserService

router = APIRouter(prefix='/user', tags=['user'])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account "
    )
async def register(user_data:User, db:AsyncSession=Depends(get_db))->UserResponse :
    """register a user"""
    try:
        service = UserService(db)

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
async def login(login_data:LoginRequest,request: Request ,db:AsyncSession=Depends(get_db)) -> LoginResponse :
    try:
        service = UserService(db)
        user=await service.login_user(login_data, request=request)

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

@router.post("/logout")
async def logout(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = UserService(db)
        return await service.logout_user(refresh_token)

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )      