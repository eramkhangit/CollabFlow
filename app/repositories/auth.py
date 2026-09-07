from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auth import UserModel, UserRole, RefreshToken
from app.schemas.auth import User, UserResponse
from typing import Optional,List, Tuple,Union
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, func
from app.models.workspace import Workspace, WorkspaceMembers, WorkspaceRole
from app.core.security import hash_password 
from datetime import datetime, timezone

updatable_fields = {"user_name", "avatar_url"}

class UserRepository:
    """Repository for user CRUD db operations"""

    def __init__(self, db:AsyncSession):
        self.db = db
 
    async def update_last_login(self, user: UserModel) -> UserModel:
       """Update user's last login timestamps"""
       try:
          user.last_login = datetime.now(timezone.utc)
          await self.db.commit()
          await self.db.refresh(user)
          return user
       except Exception:
          await self.db.rollback()
          print("Error: last_login update failed")
          raise

    async def create_user(self, user: Union[dict, User]) -> UserResponse:
      """Register a new user."""
      try:
        # Build the UserModel instance, hashing password if input is raw
        if isinstance(user, UserModel):
            user_data = user
        elif isinstance(user, dict):
            user_dict = dict(user)
            user_dict["password"] = hash_password(user_dict["password"])
            user_data = UserModel(**user_dict)
        else:
        
            user_dict = user.model_dump()
            user_dict["password"] = hash_password(user_dict["password"])
            user_data = UserModel(**user_dict)

        # verything below now runs regardless of which branch was taken
        self.db.add(user_data)
        await self.db.flush()

        workspace = Workspace(
            owner_id=user_data.id,
            name=f"{user_data.user_name}'s workspace",
        )
        self.db.add(workspace)
        await self.db.flush()

        membership = WorkspaceMembers(
            user_id=user_data.id,
            workspace_id=workspace.id,
            role=WorkspaceRole.MEMBER,
        )
        self.db.add(membership)

        await self.db.commit()
        await self.db.refresh(user_data)
        print("User Data : ", user_data)

        user_response = UserResponse(
            id=user_data.id,
            email=user_data.email,
            user_name=user_data.user_name,
            role=user_data.role,
            avatar_url=user_data.avatar_url,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            created_at=user_data.created_at,
            updated_at=user_data.updated_at,
        )

        return user_response

      except IntegrityError:
        await self.db.rollback()
        print("Error: Integrity")
        raise
      except Exception as e:
        await self.db.rollback()
        print(f"Error creating user: {e}")
        raise

    async def refresh_token( 
        self,
        user_id: str,
        jti: str,
        device_info: dict,
        expires_at
    ) -> dict:
        """Create and store refresh token, return token data instead of ORM object"""
        try:
          token = RefreshToken(
            jti=jti,
            user_id=user_id,
            device_name=device_info.get("device_name") if device_info else None,
            ip_address=device_info.get("ip_address") if device_info else None,
            user_agent=device_info.get("user_agent") if device_info else None,
            expires_at=expires_at,
            is_revoked=False
            )
  
          self.db.add(token)
          await self.db.commit()
          # Don't return ORM object - only return essential data to avoid lazy loading
          print("Token created successfully")
          return {
              "id": token.id,
              "user_id": token.user_id,
              "jti": token.jti,
              "expires_at": token.expires_at
          }

        except Exception:
            await self.db.rollback()
            print("Error: Refresh token creation failed")
            raise
 
    async def get_by_jti(self, jti:str ) -> RefreshToken | None:
        """ Get jti from db """

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def revoke_token(self, token:RefreshToken) -> RefreshToken :
        """ revoke token """
        token.is_revoked = True
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def change_pswd(self, user:UserModel, hashed_password:str) -> UserModel :

        if not user:
            raise ValueError("User doesn't exist")
        
        try:
            user.hashed_password = hashed_password 
            await self.db.commit()
            return user
        except Exception:
            await self.db.rollback()
            print("Error: password updation failed")
            raise       

    async def get_all_user_data(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
    ) -> Tuple[List[UserModel], int]:
        query = select(UserModel)
        
        if role is not None:
            query = query.where(UserModel.role == role)
        
        query = query.order_by(UserModel.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Count total
        count_query = select(func.count()).select_from(UserModel)
        if role is not None:
            count_query = count_query.where(UserModel.role == role)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        return users, total

    async def get_user_by_id(self, user_id: str) -> UserModel | None:
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.unique().scalar_one_or_none()

    async def update_user(self, user: UserModel, updates: dict) -> UserModel:
        try:
            for field, value in updates.items():
                if field in updatable_fields:
                    setattr(user, field, value)
            
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def update_role(self, user: UserModel, role: UserRole) -> UserModel:
       """Update user role"""

       if not user:
           raise ValueError("User cannot be None")
    
       try:
           user.role = role
           await self.db.commit()
           await self.db.refresh(user)
        
           return user
        
       except IntegrityError as e:
           await self.db.rollback()
           print(f"Integrity error while updating role: {e}")
           raise
        
       except Exception as e:
           await self.db.rollback()
           print(f"Error updating role for user {user.id}: {e}")
           raise
 
    async def update_avatar(self, user:UserModel, avatar:str) -> UserModel : 

        try:
            user.avatar_url = avatar
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception:
            await self.db.rollback()
            print("Error : Avatar url updation failed")
            raise      

    # soft delete
    async def set_activate(self, user:UserModel, is_active:bool) -> UserModel :

        try:
            user.is_active = is_active
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception:
            await self.db.rollback()
            print("Error : user activation failed")
            raise      

    # hard delete 
    async def delete_user(self, user:UserModel) -> None:
        try:
            self.db.delete(user)
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            print("Error : user deletion failed")
            raise     

    async def get_by_username_or_email(self, username: str, email: str) -> UserModel | None:
      """Check duplicate username or email"""
    
      # Validate input
      if not username and not email:
        raise ValueError("Either username or email is required")
    
      try:
        # Build query
        query = select(UserModel).where(
            (UserModel.email == email) | (UserModel.user_name == username)
        )
        
        #  Execute async query
        result = await self.db.execute(query)
        
        # Get first result 
        user = result.scalars().first()
        return user
        
      except SQLAlchemyError as e:
        # Database error - rollback not needed for SELECT
        print(f"Database error fetching user by username/email: {e}")
        raise
        
      except Exception as e:
        print(f"Unexpected error fetching user: {e}")
        raise
    
    async def count_users(self, 
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None
    ) -> int:
      """Count users with optional filters"""
    
      try:
        query = select(func.count()).select_from(UserModel)
        
        if role is not None:
            query = query.where(UserModel.role == role)
        
        if is_active is not None:
            query = query.where(UserModel.is_active == is_active)
        
        if is_verified is not None:
            query = query.where(UserModel.is_verified == is_verified)
        
        # Execute async query
        result = await self.db.execute(query)
        
        #  Get count value
        count = result.scalar()
        
        return count if count is not None else 0
        
      except SQLAlchemyError as e:
        print(f"Database error while counting users: {e}")
        raise
      except Exception as e:
        print(f"Unexpected error while counting users: {e}")
        raise

    async def revoke_all_tokens(self, user_id: str) -> None:
       """Revoke all active refresh tokens for a user (used in reuse-detection / security breach)"""
       try:
            result = await self.db.execute(
                select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
                )
            )
            tokens = result.scalars().all()

            for token in tokens:
               token.is_revoked = True

            await self.db.commit()

       except Exception:
            await self.db.rollback()
            print("Error: revoking all tokens failed")
            raise  