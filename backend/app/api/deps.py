from __future__ import annotations
from app.database import get_db
from app.redis import get_redis
from app.config import settings

def get_settings():
    return settings

__all__ = ["get_db", "get_redis", "get_settings"]
