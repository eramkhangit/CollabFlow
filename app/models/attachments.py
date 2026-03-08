from app.core.database import Base
from sqlalchemy import Column, String, Enum, DateTime,BigInteger,Boolean,Integer ,ForeignKey,Text
from sqlalchemy.sql import func
import uuid
import enum
from sqlalchemy.orm import relationship

class AccessLevel(str, enum.Enum):
    private = "private"
    team = "team"
    project = "project"
    public = "public"   

class Attachments(Base):
    __tablename__='attachments'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # metadata
    file_name=Column(String(1000), nullable=False)
    file_link=Column(String(1000), nullable=True)
    file_size=Column(BigInteger,nullable=False)
    mime_type=Column(String(200), nullable=False) # MIME type or extension
    file_extension=Column(String(50), nullable=True)

    description=Column(Text,nullable=True)
    
    # soft del
    is_deleted=Column(Boolean, default=False, nullable=True)

    # who can access ?
    access_level=Column(Enum(AccessLevel), default=AccessLevel.project)

    # Storage
    storage_path = Column(String(1000), nullable=False) # Relative path from upload root
    storage_type = Column(String(50), default='local') # 'local', 's3', etc.

    # permissions
    task_id = Column(String, ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True)

    # timestamps
    created_at=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at=Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    uploaded_by=Column(Integer, ForeignKey('user.id', ondelete='SET NULL'), index=True)