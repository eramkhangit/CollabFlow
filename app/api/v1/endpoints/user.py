from fastapi import APIRouter
from app.core.database import get_db
from sqlalchemy.orm import Session

route = APIRouter(prefix='/user', tags=['user'])

# def get_user_db_service(db: Session = Depends(get_db)) -> :
       