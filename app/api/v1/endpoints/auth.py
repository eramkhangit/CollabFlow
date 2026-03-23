from fastapi import APIRouter
from app.core.database import get_db
from sqlalchemy.orm import Session
from fastapi import status,Depends, HTTPException
from app.schemas.auth import UserResponse, User
from app.services.auth import UserService

router = APIRouter(prefix='/user', tags=['user'])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account "
    )
async def register(user_data:User, db:Session=Depends(get_db)) -> UserResponse :
    """register a user"""
    try:
        service = UserService(db)
        user=service.create_user(user_data)
        if user is None:
            # logger.error("User creation returned None")
            print("User creation returned None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed"
            )

        print(f"✅ User created : {user.user_name}" )
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )



       