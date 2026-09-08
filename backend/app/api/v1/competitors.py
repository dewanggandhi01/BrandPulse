from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db
from app.models.brand import Brand, BrandUrl
from app.models.competitor import Competitor
from app.models.snapshot import Snapshot
from app.models.seo_audit import SeoAudit
from app.models.product import Product
from app.models.scrape_job import ScrapeJob
from app.schemas.competitor import (
    CompetitorLinkCreate,
    CompetitorRead,
    BrandBenchmarkProfile,
    CompetitorComparisonMatrix,
    CompetitorSyncResponse,
)

logger = structlog.get_logger()
router = APIRouter()

CURRENCY_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.28,
    "INR": 0.0118,
    "CAD": 0.74,
    "AUD": 0.65,
    "JPY": 0.0066,
}

async def _get_brand_profile(brand_id: uuid.UUID, db: AsyncSession) -> BrandBenchmarkProfile:
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")

    # 1. Latest SEO audit
    q_seo = (
        select(SeoAudit)
        .join(Snapshot, SeoAudit.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .order_by(SeoAudit.audited_at.desc())
        .limit(1)
    )
    res_seo = await db.execute(q_seo)
    seo_audit = res_seo.scalar_one_or_none()

    # If no SEO audit found but a snapshot exists, compute on-the-fly and persist
    if not seo_audit:
        q_snap = (
            select(Snapshot)
            .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
            .where(BrandUrl.brand_id == brand_id)
            .order_by(Snapshot.captured_at.desc())
            .limit(1)
        )
        res_snap = await db.execute(q_snap)
        snap = res_snap.scalar_one_or_none()
        if snap and snap.html_path:
            try:
                from workers.seo import SeoAuditEngine
                brand_url_rec = await db.get(BrandUrl, snap.brand_url_id)
                target_url = brand_url_rec.url if brand_url_rec else f"https://{brand.domain}"
                audit_result = SeoAuditEngine.audit(snap.html_path, target_url)
                now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                new_audit = SeoAudit(
                    id=uuid.uuid4(),
                    snapshot_id=snap.id,
                    total_score=audit_result.get("total_score", 0),
                    technical_scores=audit_result.get("technical_scores", {}),
                    content_scores=audit_result.get("content_scores", {}),
                    structured_data_scores=audit_result.get("structured_data_scores", {}),
                    link_scores=audit_result.get("link_scores", {}),
                    issues=audit_result.get("issues", []),
                    audited_at=now_naive
                )
                db.add(new_audit)
                await db.commit()
                seo_audit = new_audit
            except Exception as e:
                logger.warning("Could not compute on-the-fly SEO audit", brand_id=str(brand_id), error=str(e))

    tech_score = None
    content_score = None
    struct_score = None
    link_score = None
    total_score = None

    if seo_audit:
        total_score = seo_audit.total_score
        tech_score = (seo_audit.technical_scores or {}).get("score")
        content_score = (seo_audit.content_scores or {}).get("score")
        struct_score = (seo_audit.structured_data_scores or {}).get("score")
        link_score = (seo_audit.link_scores or {}).get("score")

    # 2. Product Catalog Stats
    q_prod = select(
        func.count(Product.id).label("total"),
        func.avg(Product.current_price).label("avg_price"),
        func.min(Product.current_price).label("min_price"),
        func.max(Product.current_price).label("max_price"),
    ).where(Product.brand_id == brand_id)
    res_prod = await db.execute(q_prod)
    prod_row = res_prod.first()

    total_prods = prod_row[0] if prod_row and prod_row[0] is not None else 0
    avg_p = float(prod_row[1]) if prod_row and prod_row[1] is not None else None
    min_p = float(prod_row[2]) if prod_row and prod_row[2] is not None else None
    max_p = float(prod_row[3]) if prod_row and prod_row[3] is not None else None

    # In-stock rate
    in_stock_rate = None
    if total_prods > 0:
        q_stock = select(func.count(Product.id)).where(
            Product.brand_id == brand_id,
            func.lower(Product.availability).in_(["instock", "in_stock"])
        )
        res_stock = await db.execute(q_stock)
        stock_count = res_stock.scalar() or 0
        in_stock_rate = round(float(stock_count / total_prods) * 100, 1)

    # Dominant currency
    q_curr = select(Product.currency).where(Product.brand_id == brand_id, Product.currency.isnot(None)).limit(1)
    res_curr = await db.execute(q_curr)
    curr_val = res_curr.scalar()
    dominant_curr = curr_val if isinstance(curr_val, str) else "USD"

    return BrandBenchmarkProfile(
        brand_id=brand.id,
        brand_name=brand.name,
        domain=brand.domain,
        seo_total_score=total_score,
        technical_score=tech_score,
        content_score=content_score,
        structured_data_score=struct_score,
        link_score=link_score,
        product_count=total_prods,
        avg_price=round(avg_p, 2) if avg_p else None,
        min_price=round(min_p, 2) if min_p else None,
        max_price=round(max_p, 2) if max_p else None,
        currency=dominant_curr,
        in_stock_rate=in_stock_rate
    )

@router.get("/brand/{brand_id}", response_model=List[CompetitorRead])
async def list_linked_competitors(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all competitors linked to a brand."""
    query = (
        select(Competitor, Brand)
        .join(Brand, Competitor.competitor_brand_id == Brand.id)
        .where(Competitor.brand_id == brand_id)
        .order_by(Competitor.created_at.desc())
    )
    res = await db.execute(query)
    rows = list(res.all())

    results = []
    for comp, comp_brand in rows:
        results.append(CompetitorRead(
            id=comp.id,
            brand_id=comp.brand_id,
            competitor_brand_id=comp.competitor_brand_id,
            competitor_name=comp_brand.name,
            competitor_domain=comp_brand.domain,
            industry=comp_brand.industry,
            created_at=comp.created_at
        ))
    return results

@router.post("/brand/{brand_id}/link", response_model=CompetitorRead, status_code=201)
async def link_competitor_brand(
    brand_id: uuid.UUID,
    req: CompetitorLinkCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Links a competitor brand to the current brand."""
    if brand_id == req.competitor_brand_id:
        raise HTTPException(status_code=400, detail="Cannot link a brand as a competitor to itself.")

    # Verify both brands exist
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")

    comp_brand = await db.get(Brand, req.competitor_brand_id)
    if not comp_brand:
        raise HTTPException(status_code=404, detail=f"Competitor brand {req.competitor_brand_id} not found")

    # Check existing link
    q_exist = select(Competitor).where(
        Competitor.brand_id == brand_id,
        Competitor.competitor_brand_id == req.competitor_brand_id
    )
    res_exist = await db.execute(q_exist)
    if res_exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Competitor already linked to this brand.")

    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    link = Competitor(
        id=uuid.uuid4(),
        brand_id=brand_id,
        competitor_brand_id=req.competitor_brand_id,
        created_at=now_naive,
        updated_at=now_naive
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    # Auto-dispatch crawl if competitor has no snapshot data yet
    q_snap_cnt = select(func.count(Snapshot.id)).join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id).where(BrandUrl.brand_id == req.competitor_brand_id)
    res_snap_cnt = await db.execute(q_snap_cnt)
    snap_count = res_snap_cnt.scalar() or 0

    if snap_count == 0:
        try:
            target_seed = f"https://{comp_brand.domain.strip()}"
            brand_url = BrandUrl(
                id=uuid.uuid4(),
                brand_id=comp_brand.id,
                url=target_seed,
                url_type="seed",
                is_active=True,
                created_at=now_naive
            )
            db.add(brand_url)
            await db.commit()

            job = ScrapeJob(
                id=uuid.uuid4(),
                brand_id=comp_brand.id,
                job_type="website",
                status="pending",
                config={"seed_urls": [target_seed], "max_depth": 1, "max_pages": 5, "tier": "auto"},
                created_at=now_naive
            )
            db.add(job)
            await db.commit()

            from workers.tasks.scraping.website_crawler import crawl_website
            crawl_website.apply_async(
                kwargs={
                    "job_id": str(job.id),
                    "brand_id": str(comp_brand.id),
                    "seed_urls": [target_seed],
                    "max_depth": 1,
                    "max_pages": 5,
                    "tier": "auto"
                },
                queue="scraping"
            )
            logger.info("Auto-dispatched initial crawl for new competitor", brand=comp_brand.name)
        except Exception as e:
            logger.warning("Could not auto-dispatch competitor initial crawl", error=str(e))

    return CompetitorRead(
        id=link.id,
        brand_id=link.brand_id,
        competitor_brand_id=link.competitor_brand_id,
        competitor_name=comp_brand.name,
        competitor_domain=comp_brand.domain,
        industry=comp_brand.industry,
        created_at=link.created_at
    )

@router.delete("/{link_id}", status_code=204)
async def unlink_competitor(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Unlinks a competitor relationship."""
    link = await db.get(Competitor, link_id)
    if not link:
        raise HTTPException(status_code=404, detail=f"Competitor link {link_id} not found")

    await db.delete(link)
    await db.commit()

@router.post("/brand/{brand_id}/sync", response_model=CompetitorSyncResponse)
async def sync_competitors_intelligence(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Trigger background crawls/audits for target brand and all linked competitors."""
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")

    # Get all linked competitors
    q_comps = select(Competitor.competitor_brand_id).where(Competitor.brand_id == brand_id)
    res_comps = await db.execute(q_comps)
    comp_ids = list(res_comps.scalars().all())

    all_brand_ids = [brand_id] + comp_ids
    job_ids = []
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    for b_id in all_brand_ids:
        b = await db.get(Brand, b_id)
        if not b:
            continue

        # Check for active seed url
        q_url = select(BrandUrl).where(BrandUrl.brand_id == b_id, BrandUrl.is_active == True).limit(1)
        res_url = await db.execute(q_url)
        brand_url = res_url.scalar_one_or_none()

        clean_domain = b.domain.strip().replace("http://", "").replace("https://", "").rstrip("/")
        target_seed = brand_url.url if brand_url else f"https://{clean_domain}"
        if not brand_url:
            brand_url = BrandUrl(
                id=uuid.uuid4(),
                brand_id=b_id,
                url=target_seed,
                url_type="seed",
                is_active=True,
                created_at=now_naive
            )
            db.add(brand_url)
            await db.commit()

        # Create scrape job
        job = ScrapeJob(
            id=uuid.uuid4(),
            brand_id=b_id,
            job_type="website",
            status="pending",
            config={
                "seed_urls": [target_seed],
                "max_depth": 1,
                "max_pages": 5,
                "tier": "auto"
            },
            created_at=now_naive
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_ids.append(job.id)

        try:
            from workers.tasks.scraping.website_crawler import crawl_website
            crawl_website.apply_async(
                kwargs={
                    "job_id": str(job.id),
                    "brand_id": str(b.id),
                    "seed_urls": [target_seed],
                    "max_depth": 1,
                    "max_pages": 5,
                    "tier": "auto"
                },
                queue="scraping"
            )
            logger.info("Enqueued crawl_website Celery task for sync", job_id=str(job.id), brand_id=str(b.id))
        except Exception as exc:
            logger.warning("Could not dispatch Celery task: %s", exc)

    return CompetitorSyncResponse(
        message=f"Sync initiated for {len(all_brand_ids)} brand(s). Background crawls and audits dispatched.",
        synced_brands=len(all_brand_ids),
        jobs_dispatched=len(job_ids),
        job_ids=job_ids
    )

@router.get("/brand/{brand_id}/compare", response_model=CompetitorComparisonMatrix)
async def get_competitor_comparison_matrix(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Generates a side-by-side benchmarking matrix comparing target brand vs competitors."""
    target_profile = await _get_brand_profile(brand_id, db)

    # Fetch all linked competitors
    q_comps = (
        select(Competitor.competitor_brand_id)
        .where(Competitor.brand_id == brand_id)
    )
    res_comps = await db.execute(q_comps)
    comp_ids = list(res_comps.scalars().all())

    competitor_profiles: List[BrandBenchmarkProfile] = []
    for c_id in comp_ids:
        try:
            profile = await _get_brand_profile(c_id, db)
            competitor_profiles.append(profile)
        except Exception:
            continue

    # Calculate price index with currency normalization
    price_index = None
    if target_profile.avg_price and competitor_profiles:
        target_rate = CURRENCY_TO_USD.get(target_profile.currency or "USD", 1.0)
        target_usd = target_profile.avg_price * target_rate

        comp_usd_prices = []
        for c in competitor_profiles:
            if c.avg_price is not None:
                c_rate = CURRENCY_TO_USD.get(c.currency or "USD", 1.0)
                comp_usd_prices.append(c.avg_price * c_rate)

        if comp_usd_prices:
            avg_comp_usd = sum(comp_usd_prices) / len(comp_usd_prices)
            if avg_comp_usd > 0:
                price_index = round((target_usd / avg_comp_usd) * 100, 1)

    # Construct multi-brand Radar Chart data
    # Pillars: Technical, Content, Structured Data, Links
    pillars = [
        ("Technical", "technical_score"),
        ("Content", "content_score"),
        ("Structured Data", "structured_data_score"),
        ("Links", "link_score"),
    ]

    radar_data = []
    for pillar_label, attr in pillars:
        row: Dict[str, Any] = {
            "pillar": pillar_label,
            target_profile.brand_name: getattr(target_profile, attr) or 0
        }
        for comp in competitor_profiles:
            row[comp.brand_name] = getattr(comp, attr) or 0
        radar_data.append(row)

    return CompetitorComparisonMatrix(
        target_brand=target_profile,
        competitors=competitor_profiles,
        price_index=price_index,
        radar_data=radar_data
    )
