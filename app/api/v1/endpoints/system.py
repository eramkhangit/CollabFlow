from fastapi import APIRouter, Depends
from sqlalchemy import text
from fastapi import Response
from pydantic import BaseModel
from app.core.database import get_db
from typing import Any
from datetime import datetime,timezone
from sqlalchemy.ext.asyncio import AsyncSession

class HealthCeckResponse(BaseModel):
  db:str

router = APIRouter(tags=['user'])

@router.get("/health", response_model=dict[str, Any])
async def get_system_health(response: Response, db: AsyncSession = Depends(get_db) ) -> dict[str, Any]:
    """system health — API, database"""

    health_data: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "healthy",
        "success": True,
        "message": "Health check completed",
        "components": {},
    }

    # API
    health_data["components"]["api"] = {"status": "healthy"}

    # Database
    try:
        #  db = next(get_db())
        #  db.execute(text("SELECT 1"))

         # Execute async query
         await db.execute(text("SELECT 1"))

         health_data["components"]["database"] = { "status": "healthy"}

    except Exception as e:
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": "Database connection failed",
            "detail": str(e) 
        }

    # Determine overall status from components
    component_statuses = [
        comp.get("status", "unknown")
        for comp in health_data["components"].values()
    ]

    if "unhealthy" in component_statuses:
        health_data["status"] = "unhealthy"
        response.status_code = 503         
    elif "degraded" in component_statuses:
        health_data["status"] = "degraded"
        response.status_code = 503

    return health_data