from fastapi import FastAPI
from app.api.v1.endpoints import auth , system, workspace
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CollabFlow",
    version="1.0.0",
    description="CollabFlow API with FastAPI, SQLAlchemy, and MySQL",
    # lifespan=lifespan,
    docs_url="/api/docs" ,
    redoc_url="/api/redoc" ,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(workspace.router, prefix="/api/v1")
app.include_router(system.router)