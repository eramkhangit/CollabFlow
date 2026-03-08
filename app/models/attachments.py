from app.core.database import Base
from sqlalchemy import Column, String, Integer, DateTime,Enum, ForeignKey,Text
from sqlalchemy.sql import func
import enum
import uuid


class Attachments(Base):
    __tablename__='attachments'
    id=Column()