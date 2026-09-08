from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from math import ceil
from typing import TypeVar, Any

async def paginate(db: AsyncSession, query: Any, page: int, size: int) -> dict:
    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query) or 0
    
    items_query = query.limit(size).offset((page - 1) * size)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    pages = ceil(total / size) if total > 0 else 0
    
    return {
        "items": list(items),
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }
