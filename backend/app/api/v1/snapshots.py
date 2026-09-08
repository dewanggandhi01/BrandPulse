from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Optional
import uuid

from app.api.deps import get_db
from app.models.snapshot import Snapshot
from app.models.brand import BrandUrl
from app.schemas.snapshot import SnapshotRead, SnapshotDetailRead, SnapshotListResponse
from app.utils.pagination import paginate

router = APIRouter()

@router.get("", response_model=SnapshotListResponse)
async def list_snapshots(
    job_id: Optional[uuid.UUID] = None,
    brand_url_id: Optional[uuid.UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    query = select(Snapshot).order_by(Snapshot.captured_at.desc())
    if job_id:
        query = query.where(Snapshot.scrape_job_id == job_id)
    if brand_url_id:
        query = query.where(Snapshot.brand_url_id == brand_url_id)

    return await paginate(db, query, page, size)

@router.get("/brand/{brand_id}", response_model=SnapshotListResponse)
async def list_brand_snapshots(
    brand_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    query = (
        select(Snapshot)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .order_by(Snapshot.captured_at.desc())
    )
    return await paginate(db, query, page, size)

@router.get("/{snapshot_id}", response_model=SnapshotDetailRead)
async def get_snapshot(snapshot_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    snap = await db.get(Snapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return SnapshotDetailRead(
        id=snap.id,
        brand_url_id=snap.brand_url_id,
        scrape_job_id=snap.scrape_job_id,
        content_hash=snap.content_hash,
        html_size=snap.html_size,
        status_code=snap.status_code,
        headers=snap.headers,
        captured_at=snap.captured_at,
        html_content=snap.html_path
    )
