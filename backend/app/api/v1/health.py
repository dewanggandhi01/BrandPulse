from __future__ import annotations
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_redis
import redis.asyncio as redis

router = APIRouter()

@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    result = {"status": "ok", "db": "ok", "redis": "ok"}
    is_healthy = True

    try:
        await db.execute(text("SELECT 1"))
        result["db"] = "ok"
    except Exception as e:
        result["db"] = f"error: {str(e)}"
        is_healthy = False

    try:
        await redis_client.ping()
        result["redis"] = "ok"
    except Exception as e:
        result["redis"] = f"error: {str(e)}"
        is_healthy = False

    if not is_healthy:
        result["status"] = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result
