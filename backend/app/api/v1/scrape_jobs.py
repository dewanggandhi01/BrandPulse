from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Optional
import uuid
import structlog

from app.api.deps import get_db
from app.models.scrape_job import ScrapeJob
from app.models.brand import Brand
from app.schemas.scrape_job import ScrapeJobCreate, ScrapeJobRead, ScrapeJobListResponse
from app.utils.pagination import paginate

logger = structlog.get_logger()
router = APIRouter()

@router.post("", response_model=ScrapeJobRead, status_code=202)
async def create_scrape_job(job_in: ScrapeJobCreate, db: AsyncSession = Depends(get_db)) -> Any:
    # 1. Validate Brand exists
    brand = await db.get(Brand, job_in.brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {job_in.brand_id} not found")

    # Determine seed URLs: if not supplied, use brand domain
    seed_urls = job_in.seed_urls
    if not seed_urls:
        domain = brand.domain.strip()
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"
        seed_urls = [domain]

    # 2. Create ScrapeJob record
    config_dict = {
        "seed_urls": seed_urls,
        "max_depth": job_in.max_depth,
        "max_pages": job_in.max_pages,
        "tier": job_in.tier
    }

    from datetime import datetime, timezone

    job = ScrapeJob(
        id=uuid.uuid4(),
        brand_id=job_in.brand_id,
        job_type=job_in.job_type,
        status="pending",
        config=config_dict,
        created_at=datetime.utcnow()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 3. Enqueue Celery Task
    try:
        from workers.tasks.scraping.website_crawler import crawl_website
        crawl_website.apply_async(
            kwargs={
                "job_id": str(job.id),
                "brand_id": str(brand.id),
                "seed_urls": seed_urls,
                "max_depth": job_in.max_depth,
                "max_pages": job_in.max_pages,
                "tier": job_in.tier
            },
            queue="scraping"
        )
        logger.info("Enqueued crawl_website Celery task", job_id=str(job.id), brand_id=str(brand.id))
    except Exception as exc:
        logger.warning("Could not dispatch to Celery broker (broker may be offline): %s", exc)

    return job

@router.get("", response_model=ScrapeJobListResponse)
async def list_scrape_jobs(
    brand_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    query = select(ScrapeJob).order_by(ScrapeJob.created_at.desc())
    if brand_id:
        query = query.where(ScrapeJob.brand_id == brand_id)
    if status:
        query = query.where(ScrapeJob.status == status)

    return await paginate(db, query, page, size)

@router.get("/{job_id}", response_model=ScrapeJobRead)
async def get_scrape_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    job = await db.get(ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job
