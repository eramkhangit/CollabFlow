from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.users import User
from app.schemas.users import User
# from app.core.security import get_password_hash
# from sqlalchemy.exc import IntegrityError # Database constraint violation error (like duplicate email)

class UserSevice:
    @staticmethod
    def create_user() :
        pass

    def update_user():
        pass

    def delete_user():
        pass
    
    def get_all_user():
        pass