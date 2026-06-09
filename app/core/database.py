from app.config.config import get_settings
from sqlalchemy import text
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

settings = get_settings()

engine = create_async_engine(
    settings.DB_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    echo=settings.DEBUG
)

async_session_factory = async_sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession
)

# parent class used to store all metadata for all db models
Base = declarative_base()

# for apis req dep
async def get_db() -> AsyncGenerator[AsyncSession ,None]:
    async with async_session_factory () as db:
        try:
            yield db
            await db.commit()
        except Exception as e :
            await db.rollback()
            raise e   
        finally:
            await db.close() 
      

# verify connection
async def test_connection():
    try:
        # open a connection and  Use async engine with async connect
        async with engine.connect() as conn:
            # Run a simple query to verify the DB responds
            await conn.execute(text("SELECT 1"))
            # logger.info("✅ Database connection and query successful!")
            print("✅ Database connection and query successful!")
        return True
    except Exception:
        # logger.error(f"❌ Database connection failed: {e}")
        print(f"❌ Database connection failed")
        return False

async def dispose_engine():
    """Clean up connections on app shutdown"""
    await engine.dispose()