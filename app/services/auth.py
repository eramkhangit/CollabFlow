from fastapi import HTTPException, status,Request,Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auth import UserModel,UserRole
from app.schemas.auth import User, LoginRequest,UserResponse
from app.repositories.auth import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token,decode_refresh_token
from typing import Optional
from sqlalchemy.exc import IntegrityError # used for DB constraint violation error (like duplicate email)
from datetime import datetime, timezone,timedelta
import uuid
from app.config.config import get_settings
from jose import jwt, JWTError
from sqlalchemy import select
import logging
logger = logging.getLogger(__name__)

settings = get_settings()

class UserService:

    """service layer for user"""

    def __init__(self, db:AsyncSession):
        self.db = db
        self.repo = UserRepository(db)  # Repository instance

    async def create_user(self, user_data:User) -> UserResponse :
       
       existing_user= await self.repo.get_by_username_or_email(
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
           return await self.repo.create_user(db_user)
       except IntegrityError :
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account could not be created due to a conflict. Please try again."
    )
    
    async def login_user(self, login_data:LoginRequest, request: Request,response: Response) -> dict :
      
    #  check existing user
       existing_user= await self.repo.get_by_username_or_email(
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

       existing_user = await self.repo.update_last_login(existing_user)
       
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
       await self.repo.refresh_token(
           user_id=str(existing_user.id),
           jti=jti,
           device_info=device_info,
           expires_at=expires_at
       )

     # ✅ Set refresh token as HttpOnly cookie (not in JSON body)
       response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,                 
        secure=False,                   # make True in production
        samesite="strict",             # CSRF se bachaata hai; "lax" bhi chalega agar cross-site nav chahiye
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        # path="/api/v1/user/refresh-token"       # cookie only send on refresh endpoint 
        path="/"     
      )

       return {
        "user": {
            "id": str(existing_user.id),
            "user_name": existing_user.user_name,
            "email": existing_user.email
        },
        "access_token": access_token,
        "token_type": "bearer"
    }

    async def refresh_access_token(self, request: Request, response: Response) -> dict:

       refresh_token_str = request.cookies.get("refresh_token")

       if not refresh_token_str:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

       payload = decode_refresh_token(refresh_token_str)
       user_id = payload.get("sub")
       jti = payload.get("jti")

       if not user_id or not jti:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

       stored_token = await self.repo.get_by_jti(jti) 

       if not stored_token:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found, please login again")

       # Check if token is revoked
       if stored_token.is_revoked:  # Fixed: changed from 'revoked' to 'is_revoked'
           raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    
       # Check if token is expired (with timezone handling)
       now_utc = datetime.now(timezone.utc)
       if stored_token.expires_at.replace(tzinfo=timezone.utc) < now_utc:
           raise HTTPException(status_code=401, detail="Refresh token has expired")

       user = await self.repo.get_user_by_id(user_id) # ✅ get_user_by_id, no int()

       if not user or not user.is_active:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

       await self.repo.revoke_token(stored_token)  # ✅ object pass, not jti string

       new_jti = str(uuid.uuid4())
       new_refresh_token = create_refresh_token(user_id=str(user.id), jti=new_jti)

       await self.repo.refresh_token( # ✅ refresh_token, not save_refresh_token
           user_id=str(user.id),
           jti=new_jti,
           device_info={
            "device_name": request.headers.get("User-Agent", "unknown"),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        },
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
       )

       access_token = create_access_token(user_id=str(user.id), role=user.role) 
       response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        # path="/api/v1/user/refresh-token"
        path='/' # because cookie send with all requests
       )

       return {
          "access_token": access_token,
          "token_type": "bearer"
       }

    async def logout_user(self, request: Request, response: Response) -> dict:
        """Logout user - revokes refresh token and clears cookie."""
        
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            return {"message": "Already logged out"}
        
        # ✅ Use the new revoke_refresh_token method
        revoked = await self.revoke_refresh_token(refresh_token)
        
        if revoked:
            logger.info("User logged out successfully")
        else:
            logger.warning("Failed to revoke refresh token during logout")
        
        # ✅ Always clear cookie
        response.delete_cookie(
            key="refresh_token",
            path="/"
        )
        
        return {"message": "Logout successful"}
    
    async def get_user_by_id(self, user_id: str):
           """Basic user fetch - no relationships"""
    
           query = select(UserModel).where(UserModel.id == user_id)
           result = await self.db.execute(query)
           return result.unique().scalar_one_or_none()

    async def get_user_by_id_with_details(self, user_id: str):
        """User fetch with all relationships"""
    
        from sqlalchemy.orm import selectinload
    
        query = select(UserModel)\
        .where(UserModel.id == user_id)\
        .options(
            selectinload(UserModel.workspaces),
            selectinload(UserModel.workspace_members)
        )
    
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def update_user(self, user_id: str, updates: dict) -> UserResponse:
        "update specific user and specific field"
        user = await self.get_user_by_id(user_id)
        return await self.repo.update_user(
        # self,
        user,updates)

    async def delete_user(self, user_id:str) -> None :
        """delete specific user"""
        user = await self.get_user_by_id(user_id)
        await self.repo.delete_user(user) 
    
    async def get_all_user(
        self,
        skip:int = 0,
        limit:int = 100,
        role : Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        ) -> dict:

        """ return paginated list of users and count """
        users = await self.repo.get_all_user_data(
            # self, 
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active,
            is_verified=is_verified
        )

        total = await self.repo.count_users(
            # self, 
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active,
            is_verified=is_verified
        )
        return {"total":total, "skip":skip, "limit":limit,"users":users} 

    async def revoke_refresh_token(self, refresh_token_str: str) -> bool:
        """
        Revoke a refresh token by its string value.
        
        Args:
            refresh_token_str: The refresh token string from cookie
            
        Returns:
            bool: True if revoked successfully, False otherwise
            
           Security:
            - Decodes JWT to get jti
            - Validates token type is 'refresh'
            - Revokes token in database
            - Handles all errors gracefully
        """
        try:
            # Decode the token
            payload = jwt.decode(
                refresh_token_str,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # ✅ Validate token type
            if payload.get("type") != "refresh":
                logger.warning("Attempted to revoke non-refresh token")
                return False
            
            # ✅ Get jti from payload
            jti = payload.get("jti")
            if not jti:
                logger.warning("Token missing jti claim")
                return False
            
            # ✅ Find token in database
            token = await self.repo.get_by_jti(jti)
            
            if not token:
                logger.warning(f"Token not found: {jti}")
                return False
            
            # ✅ Check if already revoked
            if token.is_revoked:
                logger.info(f"Token already revoked: {jti}")
                return True
            
            # ✅ Revoke the token
            await self.repo.revoke_token(token)
            logger.info(f"Token revoked successfully: {jti}")
            return True
            
        except jwt.ExpiredSignatureError:
            logger.warning("Attempted to revoke expired token")
            return False
        except jwt.JWTError as e:
            logger.warning(f"Invalid JWT during revocation: {e}")
            return False
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return False