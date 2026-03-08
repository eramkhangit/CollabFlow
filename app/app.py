from fastapi import FastAPI

app = FastAPI(
    title="CollabFlow",
    version="1.0.0",
    description="CollabFlow API with FastAPI, SQLAlchemy, and MySQL",
    # lifespan=lifespan,
    docs_url="/api/docs" ,
    redoc_url="/api/redoc" ,
)