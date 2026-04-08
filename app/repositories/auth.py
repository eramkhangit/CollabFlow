from sqlalchemy.orm import Session
from app.models.auth import UserModel, UserRole, RefreshToken
from typing import Optional,List, Tuple,Union
from sqlalchemy.exc import IntegrityError

updatable_fields = {"username", "avatar_url"}

class UserRepository:
    """Repository for user CRUD db operations"""

    def __init__(self, db:Session):
        self.db = db
 
    def create_user(self, user:Union[dict, UserModel]) -> UserModel :
        """register a new user """
        try:
            if isinstance(user, UserModel):
              user_data = user
            else:
              # if dict then convert 
              user_data = UserModel(**user)
        
            self.db.add(user_data)
            self.db.commit()
            print((f"Registered a user with id: {user_data.id}"))
            self.db.refresh(user_data)
            return user_data 
        except IntegrityError:
            self.db.rollback()
            print('Error : Integrity ')
            raise           
        except Exception as e:
            self.db.rollback()
            print((f"Error creating todo: {e}"))
            raise

    def refresh_token( 
        self,
        user_id: str,
        jti: str,
        device_info: dict,
        expires_at
    ) -> RefreshToken:
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
          print("Befor store refresh")
          self.db.add(token)
          self.db.commit()
          self.db.refresh(token)
          print("Befor store refresh")

          return token

        except Exception:
            self.db.rollback()
            print("Error: Refresh token creation failed")
            raise

    def change_pswd(self, user:UserModel, hashed_password:str) -> UserModel :

        try:
            user.hashed_password = hashed_password 
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            print("Error: password updation failed")
            raise       

    def get_all_user_data(
        self,
        skip:int = 0,
        limit:int = 100,
        role : Optional[UserRole] = None,
        ) -> Tuple[List[UserModel], int] :

        """Get all users from db with filters """ 

        query = self.db.query(UserModel)  

        if role is not None :
            query = query.filter(UserModel.role == role)    

        return (
            query
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )      

    def update_user(self, user:UserModel, updates:dict) -> UserModel:
           try : 
                for field, value in updates.items():
                     if field in updatable_fields:
                         setattr(user,field , value)

                self.db.commit()  
                self.db.refresh(user)
                return user          
           except IntegrityError:
                # updating username to one that already exists
                self.db.rollback()
                raise

           except Exception:
               # Catch-all for unexpected DB errors
               self.db.rollback()
               raise  

    def update_role(self, user:UserModel, role:UserRole) -> UserModel :

        try:
            user.role = role
            self.db.commit()
            self.db.refresh(user)
            return user
        except:
            self.db.rollback()
            print("Error : Role updation failed")
            raise   
    
    def update_avatar(self, user:UserModel, avatar:str) -> UserModel :

        try:
            user.avatar_url = avatar
            self.db.commit()
            self.db.refresh(user)
            return user
        except :
            self.db.rollback()
            print("Error : Avatar url updation failed")
            raise      

    # soft delete
    def set_activate(self, user:UserModel, is_active:bool) -> UserModel :

        try:
            user.is_active = is_active
            self.db.commit()
            self.db.refresh(user)
            return user
        except:
            self.db.rollback()
            print("Error : user activation failed")
            raise      

    # hard delete — permanently removes the row from the DB
    def delete_user(self, user:UserModel) -> None:
        try:
            self.db.delete(user)
            self.db.commit()

        except:
            self.db.rollback()
            print("Error : user deletion failed")
            raise     
  
    # user to check duplicate username or email
    def get_by_username_or_email(self, username:str, email:str) -> UserModel | None :
        try:
            return(
            self.db.query(UserModel)
            .filter(
                (UserModel.email == email) | (UserModel.user_name == username)
            )
            .first()
        )
        except : 
            print(f'Error : Error fetching user by username/email - username: {username}, email: {email}')
            raise
 
    # count users in db
    def count_users(self, 
        role:Optional[UserRole]=None,
        is_active:Optional[bool]=None,
        is_verified:Optional[bool]=None
        ) -> int :
        query = self.db.query(UserModel)

        if role is not None:
            query = query.filter(UserModel.role == role)

        if is_active is not None:
            query = query.filter(UserModel.is_active == is_active)

        if is_verified is not None:
            query = query.filter(UserModel.is_verified == is_verified)

        return query.count()
    
    # get specific user
    def get_user_by_id(
            self,
            user_id:str
        ) -> UserModel | None :
        return(
            self.db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )