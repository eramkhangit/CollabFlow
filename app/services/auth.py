from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.auth import UserModel,UserRole
from app.schemas.auth import User
from app.repositories.auth import UserRepository
from app.core.security import hash_password
from typing import Tuple, Optional,List
from sqlalchemy.exc import IntegrityError # used for DB constraint violation error (like duplicate email)

class UserService:

    """service layer for user"""

    def __init__(self, db:Session):
        self.db = db
        self.repo = UserRepository(db)  # Repository instance

    def create_user(self, user_data:User) -> UserModel :
       
       existing_user=self.repo.get_by_username_or_email(
           email=user_data.email , 
           username=user_data.user_name)
       
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