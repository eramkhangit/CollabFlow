from fastapi import FastAPI
from app.api.v1.endpoints import auth , system


app = FastAPI(
    title="CollabFlow",
    version="1.0.0",
    description="CollabFlow API with FastAPI, SQLAlchemy, and MySQL",
    # lifespan=lifespan,
    docs_url="/api/docs" ,
    redoc_url="/api/redoc" ,
)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(system.router)