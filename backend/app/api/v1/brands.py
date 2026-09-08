from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any
import uuid

from app.api.deps import get_db
from app.models.brand import Brand, BrandUrl
from app.models.snapshot import Snapshot
from app.schemas.brand import BrandCreate, BrandUpdate, BrandRead, BrandListResponse
from app.schemas.snapshot import SnapshotListResponse
from app.utils.pagination import paginate

router = APIRouter()

@router.post("", response_model=BrandRead, status_code=201)
async def create_brand(brand_in: BrandCreate, db: AsyncSession = Depends(get_db)) -> Any:
    brand = Brand(**brand_in.model_dump())
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand

@router.get("", response_model=BrandListResponse)
async def list_brands(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100), db: AsyncSession = Depends(get_db)) -> Any:
    query = select(Brand).order_by(Brand.created_at.desc())
    return await paginate(db, query, page, size)

@router.get("/{brand_id}", response_model=BrandRead)
async def get_brand(brand_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.put("/{brand_id}", response_model=BrandRead)
async def update_brand(brand_id: uuid.UUID, brand_in: BrandUpdate, db: AsyncSession = Depends(get_db)) -> Any:
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    update_data = brand_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)
        
    await db.commit()
    await db.refresh(brand)
    return brand

@router.delete("/{brand_id}", status_code=204)
async def delete_brand(brand_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await db.delete(brand)
    await db.commit()

@router.get("/{brand_id}/snapshots", response_model=SnapshotListResponse)
async def get_brand_snapshots(
    brand_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    query = (
        select(Snapshot)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .order_by(Snapshot.captured_at.desc())
    )
    return await paginate(db, query, page, size)

