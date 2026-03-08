from app.config.config import get_settings
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session,sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator

settings = get_settings()

engine = create_engine(
    settings.DB_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    echo=settings.DEBUG
)

sessionLocal= sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

# base cls for all db models
Base = declarative_base()

# for apis req dep
def get_db() -> Generator[Session ,None,None]:
   db = sessionLocal()
   try:
      yield db
   finally:
      db.close()

# verify connection
def test_connection():
    try:
        # open a connection
        with engine.connect() as conn:
            # Run a simple query to verify the DB responds
            conn.execute(text("SELECT 1"))
            # logger.info("✅ Database connection and query successful!")
            print("✅ Database connection and query successful!")
        return True
    except Exception as e:
        # logger.error(f"❌ Database connection failed: {e}")
        print(f"❌ Database connection failed: {e}")
        return False
