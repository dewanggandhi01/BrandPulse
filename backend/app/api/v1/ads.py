from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.api.deps import get_db
from app.models.brand import Brand
from app.models.ad_intel import AdIntel
from app.schemas.ad_intel import (
    AdIntelCreate,
    AdIntelBatchCreate,
    AdIntelRead,
    AdIntelListResponse,
    AdIntelAnalyticsResponse,
    PlatformShare,
    FormatShare,
    SpendTierShare,
    TopItem,
    AdParsePreviewRequest,
    AdParsePreviewResponse
)
from workers.ads.parser import AdCreativeParser
from workers.ads.estimator import AdSpendEstimator

logger = structlog.get_logger()
router = APIRouter()

def _enrich_ad_read(ad: AdIntel) -> AdIntelRead:
    tier = AdSpendEstimator.calculate_longevity_and_tier(ad.first_seen, ad.last_seen)
    targeting = ad.targeting_info or {}
    
    headline = targeting.get("headline")
    cta = targeting.get("cta")
    if not headline and ad.ad_text:
        parser = AdCreativeParser()
        p = parser.parse_ad(ad.ad_text, ad.target_url, ad.ad_format)
        headline = p.headline
        cta = cta or p.cta

    return AdIntelRead(
        id=ad.id,
        brand_id=ad.brand_id,
        platform=ad.platform,
        ad_text=ad.ad_text,
        ad_format=ad.ad_format,
        target_url=ad.target_url,
        first_seen=ad.first_seen,
        last_seen=ad.last_seen,
        targeting_info=targeting,
        data_source_tag=ad.data_source_tag,
        created_at=ad.created_at,
        longevity_days=tier.longevity_days,
        spend_tier=tier.tier_label,
        is_evergreen=tier.is_evergreen,
        headline=headline,
        cta=cta
    )

@router.post("/parse-preview", response_model=AdParsePreviewResponse)
async def parse_ad_preview(payload: AdParsePreviewRequest) -> AdParsePreviewResponse:
    """
    Test and preview ad creative parsing, format detection, and CTA extraction on the fly.
    """
    parser = AdCreativeParser()
    p = parser.parse_ad(payload.raw_text, payload.target_url, payload.suggested_format)
    tier = AdSpendEstimator.calculate_longevity_and_tier(date.today(), date.today())

    return AdParsePreviewResponse(
        headline=p.headline,
        body_copy=p.body_copy,
        cta=p.cta,
        detected_format=p.detected_format,
        landing_page_domain=p.landing_page_domain,
        utm_parameters=p.utm_parameters,
        longevity_days=tier.longevity_days,
        spend_tier=tier.tier_label,
        is_evergreen=tier.is_evergreen
    )

@router.get("/brand/{brand_id}", response_model=AdIntelListResponse)
async def get_brand_ads(
    brand_id: uuid.UUID,
    platform: str | None = Query(None, description="Filter by platform: google, meta, linkedin"),
    ad_format: str | None = Query(None, description="Filter by format: search, display, video, sponsored_feed"),
    search: str | None = Query(None, description="Search ad text or headline"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> AdIntelListResponse:
    """
    List competitor ad creatives with platform, format, and search filtering.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    query = select(AdIntel).where(AdIntel.brand_id == brand_id)

    if platform and platform.lower() != "all":
        query = query.where(AdIntel.platform == platform.lower())

    if ad_format and ad_format.lower() != "all":
        query = query.where(AdIntel.ad_format == ad_format.lower())

    if search and search.strip():
        query = query.where(AdIntel.ad_text.ilike(f"%{search.strip()}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(desc(AdIntel.first_seen), desc(AdIntel.created_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    ads = result.scalars().all()

    enriched_items = [_enrich_ad_read(ad) for ad in ads]
    pages = (total + size - 1) // size if size > 0 else 1

    return AdIntelListResponse(
        items=enriched_items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/brand/{brand_id}", response_model=AdIntelRead, status_code=status.HTTP_201_CREATED)
async def create_brand_ad(
    brand_id: uuid.UUID,
    payload: AdIntelCreate,
    db: AsyncSession = Depends(get_db)
) -> AdIntelRead:
    """
    Ingest a new competitor ad creative, automatically parse components, and persist to database.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    parser = AdCreativeParser()
    p = parser.parse_ad(payload.ad_text or "", payload.target_url, payload.ad_format)
    tier = AdSpendEstimator.calculate_longevity_and_tier(payload.first_seen, payload.last_seen)

    targeting = payload.targeting_info or {}
    targeting.update({
        "headline": p.headline,
        "cta": p.cta,
        "landing_page_domain": p.landing_page_domain,
        "utm_parameters": p.utm_parameters,
        "longevity_days": tier.longevity_days,
        "spend_tier": tier.tier_label,
        "is_evergreen": tier.is_evergreen
    })

    now = datetime.now(timezone.utc)
    new_ad = AdIntel(
        id=uuid.uuid4(),
        brand_id=brand_id,
        platform=payload.platform.lower(),
        ad_text=payload.ad_text,
        ad_format=p.detected_format,
        target_url=payload.target_url,
        first_seen=payload.first_seen or date.today(),
        last_seen=payload.last_seen or date.today(),
        targeting_info=targeting,
        data_source_tag=payload.data_source_tag or "manual_ingest",
        created_at=now
    )
    db.add(new_ad)
    await db.commit()

    return _enrich_ad_read(new_ad)

@router.post("/brand/{brand_id}/batch", status_code=status.HTTP_201_CREATED)
async def batch_ingest_ads(
    brand_id: uuid.UUID,
    payload: AdIntelBatchCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Bulk ingest competitor ad creatives.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    parser = AdCreativeParser()
    now = datetime.now(timezone.utc)
    count = 0

    for item in payload.ads:
        p = parser.parse_ad(item.ad_text or "", item.target_url, item.ad_format)
        tier = AdSpendEstimator.calculate_longevity_and_tier(item.first_seen, item.last_seen)

        targeting = item.targeting_info or {}
        targeting.update({
            "headline": p.headline,
            "cta": p.cta,
            "landing_page_domain": p.landing_page_domain,
            "utm_parameters": p.utm_parameters,
            "longevity_days": tier.longevity_days,
            "spend_tier": tier.tier_label,
            "is_evergreen": tier.is_evergreen
        })

        new_ad = AdIntel(
            id=uuid.uuid4(),
            brand_id=brand_id,
            platform=item.platform.lower(),
            ad_text=item.ad_text,
            ad_format=p.detected_format,
            target_url=item.target_url,
            first_seen=item.first_seen or date.today(),
            last_seen=item.last_seen or date.today(),
            targeting_info=targeting,
            data_source_tag=item.data_source_tag or "batch_ingest",
            created_at=now
        )
        db.add(new_ad)
        count += 1

    await db.commit()
    return {"status": "success", "count": count, "brand_id": brand_id}

@router.get("/brand/{brand_id}/analytics", response_model=AdIntelAnalyticsResponse)
async def get_ad_analytics(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> AdIntelAnalyticsResponse:
    """
    Aggregated paid advertising intelligence: platform share, format breakdown,
    spend tiers, top CTAs, and estimated monthly spend.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    stmt = select(AdIntel).where(AdIntel.brand_id == brand_id)
    result = await db.execute(stmt)
    ads = result.scalars().all()

    raw_ads = [
        {
            "platform": a.platform,
            "ad_format": a.ad_format,
            "first_seen": a.first_seen,
            "last_seen": a.last_seen,
            "targeting_info": a.targeting_info or {}
        }
        for a in ads
    ]

    agg = AdSpendEstimator.aggregate_brand_ad_intelligence(raw_ads)

    return AdIntelAnalyticsResponse(
        brand_id=brand_id,
        total_ads=agg["total_ads"],
        evergreen_count=agg["evergreen_count"],
        platform_distribution=[
            PlatformShare(platform=p["platform"], count=p["count"], percentage=p["percentage"])
            for p in agg["platform_distribution"]
        ],
        format_distribution=[
            FormatShare(format=f["format"], count=f["count"], percentage=f["percentage"])
            for f in agg["format_distribution"]
        ],
        spend_tier_distribution=[
            SpendTierShare(tier=t["tier"], count=t["count"], percentage=t["percentage"])
            for t in agg["spend_tier_distribution"]
        ],
        top_ctas=[
            TopItem(name=c["cta"], count=c["count"])
            for c in agg["top_ctas"]
        ],
        top_landing_domains=[
            TopItem(name=d["domain"], count=d["count"])
            for d in agg["top_landing_domains"]
        ],
        estimated_monthly_spend_range=agg["estimated_monthly_spend_range"]
    )
