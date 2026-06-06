from fastapi import HTTPException, status,Request
from sqlalchemy.orm import Session
from app.models.auth import UserModel,UserRole
from app.schemas.auth import User, LoginRequest
from app.repositories.auth import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from typing import Optional
from sqlalchemy.exc import IntegrityError # used for DB constraint violation error (like duplicate email)
from datetime import datetime, timezone,timedelta
import uuid
from app.config.config import get_settings
from jose import jwt, JWTError

settings = get_settings()

class UserService:

    """service layer for user"""

    def __init__(self, db:Session):
        self.db = db
        self.repo = UserRepository(db)  # Repository instance

    def create_user(self, user_data:User) -> UserModel :
       
       existing_user=self.repo.get_by_username_or_email(
           email=user_data.email , 
           username=user_data.user_name
           )
       
    #  check existing user
       if existing_user:
           if existing_user.email == user_data.email :
               raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST, 
                   detail="Email already registered")

           raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST, 
                   detail="Username already registered")
       
        # hash new user password
       hashed_password = hash_password(user_data.password)
       
        # build orm obj
       db_user = UserModel(
            email=user_data.email,
            user_name=user_data.user_name,
            avatar_url=user_data.avatar_url,
            password=hashed_password,
            role=user_data.role,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified
        )
       
       try:
           return self.repo.create_user(db_user)
       except IntegrityError :
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account could not be created due to a conflict. Please try again."
    )
    
    def login_user(self, login_data:LoginRequest, request: Request) -> UserModel :
      
    #  check existing user
       existing_user=self.repo.get_by_username_or_email(
           email=login_data.email , 
           username=login_data.user_name
           )
       
       if not existing_user :
           
           raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED, 
                   detail="Invalid email or password")
       
    # check user active or not
       elif existing_user.is_active == False :
           raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN, 
                   detail="Inactive user") 
   
    # verify password
       if not verify_password(login_data.password, existing_user.password) :
           raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Invalid email or password" )
        
       # Create access token
       access_token = create_access_token(
                user_id=str(existing_user.id),
                role=existing_user.role)
        
       # Create refresh token with device info
       device_info = {
            "device_name": request.headers.get("User-Agent", "unknown"),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }  
       
       now = datetime.now(timezone.utc)
       jti = str(uuid.uuid4())
       expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

       refresh_token=create_refresh_token(user_id=str(existing_user.id), jti=jti)

       # save in db 
       self.repo.refresh_token(
           user_id=str(existing_user.id),
           jti=jti,
           device_info=device_info,
           expires_at=expires_at
       )

    # create refresh token with device info 
       return {
            "user": {
                "id": str(existing_user.id),
                "user_name": existing_user.user_name,
                "email": existing_user.email
               },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def logout_user(self, refresh_token: str):

      try:
        # decode token
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # check type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=400,
                detail="Invalid token type"
            )

        # get jti
        jti = payload.get("jti")

        if not jti:
            raise HTTPException(
                status_code=400,
                detail="Invalid token"
            )

        #  find in DB
        token = self.repo.get_by_jti(jti)

        if not token:
            raise HTTPException(
                status_code=404,
                detail="Token not found"
            )

        if token.is_revoked:
            raise HTTPException(
                status_code=400,
                detail="Token already revoked"
            )

        # revoke
        self.repo.revoke_token(token)

        return {"message": "Logout successful"}

      except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    def get_user_by_id(self, user_id:str) -> UserModel :
        """return user with given specific id"""
        user = self.repo.get_user_by_id(
            # self ,
            user_id)
        if not user :
           raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
            )
        return user
    
    def update_user(self, user_id: str, updates: dict) -> UserModel:
        "update specific user and specific field"
        user = self.get_user_by_id(user_id)
        return self.repo.update_user(
        # self,
        user,updates)

    def delete_user(self, user_id:str) -> None :
        """delete specific user"""
        user = self.get_user_by_id(user_id)
        self.repo.delete_user(user) 
    
    def get_all_user(
        self,
        skip:int = 0,
        limit:int = 100,
        role : Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        ) -> dict:

        """ return paginated list of users and count """
        users = self.repo.get_all_user_data(
            # self, 
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active,
            is_verified=is_verified
        )

        total = self.repo.count_users(
            # self, 
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active,
            is_verified=is_verified
        )
        return {"total":total, "skip":skip, "limit":limit,"users":users}