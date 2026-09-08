from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, List
from datetime import datetime, timezone
import uuid
import structlog

from app.api.deps import get_db
from app.models.brand import Brand, BrandUrl
from app.models.snapshot import Snapshot
from app.models.seo_audit import SeoAudit
from app.schemas.seo_audit import (
    SeoAuditRead,
    SeoAuditHistoryItem,
    SeoAuditHistoryResponse
)
from workers.seo import SeoAuditEngine

logger = structlog.get_logger()
router = APIRouter()

@router.post("/brands/{brand_id}/seo-audit/run", response_model=SeoAuditRead, status_code=201)
async def run_brand_seo_audit(
    brand_id: uuid.UUID,
    refresh: bool = Query(False, description="Force on-the-fly live fetch instead of existing snapshot"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    # 1. Verify Brand exists
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")

    snapshot = None
    brand_url = None

    if not refresh:
        # 2. Find latest snapshot
        query = (
            select(Snapshot, BrandUrl)
            .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
            .where(BrandUrl.brand_id == brand_id)
            .order_by(Snapshot.captured_at.desc())
            .limit(1)
        )
        res = await db.execute(query)
        row = res.first()
        if row:
            snapshot, brand_url = row

    # If no snapshot exists yet, or snapshot is empty, or refresh is forced: scrape on-the-fly
    if not snapshot or not (snapshot.html_path or "").strip():
        raw_domain = (brand.domain or "").strip()
        if not raw_domain:
            raise HTTPException(status_code=400, detail="Brand has no domain specified.")

        target_url = raw_domain if raw_domain.startswith(("http://", "https://")) else f"https://{raw_domain}"
        logger.info("Executing on-the-fly website fetch for SEO audit", brand_id=str(brand_id), url=target_url)

        from workers.scrapers.http_scraper import HttpScraper
        import hashlib

        scraper = HttpScraper(timeout=8.0, max_retries=1, enforce_robots=False)
        scrape_res = await scraper.scrape(target_url)

        # HTTP fallback only if HTTPS completely failed without any response
        if not scrape_res.html and (scrape_res.status_code == 0 or scrape_res.error) and target_url.startswith("https://"):
            fallback_url = f"http://{raw_domain}"
            logger.info("Retrying fetch with HTTP fallback", url=fallback_url)
            fallback_res = await scraper.scrape(fallback_url)
            if fallback_res.html:
                scrape_res = fallback_res
                target_url = fallback_url

        if not scrape_res.html and scrape_res.status_code >= 400:
            raise HTTPException(
                status_code=400,
                detail=f"Could not reach {target_url} (HTTP {scrape_res.status_code}: {scrape_res.error or 'Failed to fetch'}). Please ensure the domain is correct or run a website crawl job."
            )

        # Get or create BrandUrl entry
        b_url_query = select(BrandUrl).where(BrandUrl.brand_id == brand_id, BrandUrl.url == target_url)
        b_url_res = await db.execute(b_url_query)
        brand_url = b_url_res.scalar_one_or_none()
        if not brand_url:
            brand_url = BrandUrl(
                id=uuid.uuid4(),
                brand_id=brand_id,
                url=target_url,
                url_type="seed",
                is_active=True
            )
            db.add(brand_url)
            await db.flush()

        clean_html = (scrape_res.html or "").replace("\x00", "")
        snapshot = Snapshot(
            id=uuid.uuid4(),
            brand_url_id=brand_url.id,
            content_hash=scrape_res.content_hash or hashlib.sha256(clean_html.encode("utf-8")).hexdigest(),
            html_size=len(clean_html.encode("utf-8")),
            status_code=scrape_res.status_code or 200,
            headers=scrape_res.headers or {},
            html_path=clean_html[:1000000]
        )
        db.add(snapshot)
        await db.flush()

    # 3. Perform audit using SeoAuditEngine
    target_page_url = (
        brand_url.url
        if hasattr(brand_url, "url") and isinstance(brand_url.url, str)
        else (target_url if "target_url" in locals() and isinstance(target_url, str) else "https://unknown.com")
    )
    audit_res = SeoAuditEngine.audit(snapshot.html_path or "", target_page_url)

    # 4. Save SeoAudit record
    audit_record = SeoAudit(
        id=uuid.uuid4(),
        snapshot_id=snapshot.id,
        total_score=audit_res["total_score"],
        technical_scores=audit_res["technical_scores"],
        content_scores=audit_res["content_scores"],
        structured_data_scores=audit_res["structured_data_scores"],
        link_scores=audit_res["link_scores"],
        issues=audit_res["issues"],
        audited_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(audit_record)
    await db.commit()
    await db.refresh(audit_record)

    logger.info("Saved brand SEO audit", brand_id=str(brand_id), total_score=audit_record.total_score)
    return audit_record

@router.get("/brands/{brand_id}/seo-audit/latest", response_model=SeoAuditRead)
async def get_latest_seo_audit(brand_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    query = (
        select(SeoAudit)
        .join(Snapshot, SeoAudit.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .order_by(SeoAudit.audited_at.desc())
        .limit(1)
    )
    res = await db.execute(query)
    audit = res.scalar_one_or_none()

    if not audit:
        raise HTTPException(status_code=404, detail="No SEO audit records found for this brand")

    return audit

@router.get("/brands/{brand_id}/seo-audit/history", response_model=SeoAuditHistoryResponse)
async def get_seo_audit_history(brand_id: uuid.UUID, limit: int = Query(20, ge=2, le=100), db: AsyncSession = Depends(get_db)) -> Any:
    query = (
        select(SeoAudit)
        .join(Snapshot, SeoAudit.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .order_by(SeoAudit.audited_at.asc())
        .limit(limit)
    )
    res = await db.execute(query)
    audits = res.scalars().all()

    history_items: List[SeoAuditHistoryItem] = []
    for a in audits:
        tech_s = a.technical_scores.get("score", 0) if a.technical_scores else 0
        content_s = a.content_scores.get("score", 0) if a.content_scores else 0
        struct_s = a.structured_data_scores.get("score", 0) if a.structured_data_scores else 0
        link_s = a.link_scores.get("score", 0) if a.link_scores else 0

        history_items.append(
            SeoAuditHistoryItem(
                id=a.id,
                total_score=a.total_score,
                technical_score=tech_s,
                content_score=content_s,
                structured_data_score=struct_s,
                link_score=link_s,
                audited_at=a.audited_at
            )
        )

    latest_score = history_items[-1].total_score if history_items else None
    return SeoAuditHistoryResponse(
        items=history_items,
        brand_id=brand_id,
        latest_score=latest_score
    )

@router.get("/seo-audit/{audit_id}", response_model=SeoAuditRead)
async def get_seo_audit_by_id(audit_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    audit = await db.get(SeoAudit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="SEO audit record not found")
    return audit
