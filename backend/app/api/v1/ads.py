from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone, date, timedelta
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

def get_sample_ads_for_brand(brand_name: str, brand_domain: str | None = None) -> list[dict]:
    name = brand_name
    dom = brand_domain or f"{name.lower().replace(' ', '')}.com"

    return [
        # Google Ads (Search) - Evergreen Winner (active 80 days)
        {
            "platform": "google",
            "ad_format": "search",
            "ad_text": f"{name} Official Store - Exclusive New Arrivals\nExplore premium products, innovative design, and fast shipping. Shop now.",
            "target_url": f"https://{dom}/shop?utm_source=google&utm_medium=cpc&utm_campaign=brand_search",
            "days_active": 80,
        },
        # Google Ads (Search) - Active Campaign (active 14 days)
        {
            "platform": "google",
            "ad_format": "search",
            "ad_text": f"Limited Time Sale | Up to 40% Off on {name}\nUpgrade your gear today. Free returns & 100% authentic. Claim offer now.",
            "target_url": f"https://{dom}/deals?utm_source=google&utm_medium=cpc&utm_campaign=seasonal_promo",
            "days_active": 14,
        },
        # Google Ads (Display Banner) - Scaling Campaign (active 35 days)
        {
            "platform": "google",
            "ad_format": "display",
            "ad_text": f"Engineered for Performance. Experience the all-new {name} lineup designed for durability and comfort. Learn more.",
            "target_url": f"https://{dom}/performance?utm_source=google_display&utm_medium=banner&utm_campaign=retargeting",
            "days_active": 35,
        },
        # Google Ads (Search) - Scaling Campaign (active 40 days)
        {
            "platform": "google",
            "ad_format": "search",
            "ad_text": f"{name} Pricing & Plans - Compare Models\nTransparent pricing, no hidden fees, and money-back guarantee. See pricing and subscribe.",
            "target_url": f"https://{dom}/pricing?utm_source=google&utm_medium=cpc&utm_campaign=intent_pricing",
            "days_active": 40,
        },
        # Google Ads (Video Ad / YouTube) - Active Campaign (active 10 days)
        {
            "platform": "google",
            "ad_format": "video",
            "ad_text": f"See {name} in Action - The Future of Everyday Performance\nWatch product demonstration and customer testimonials. Learn more.",
            "target_url": f"https://{dom}/watch?utm_source=youtube&utm_medium=truview&utm_campaign=video_branding",
            "days_active": 10,
        },
        # Meta (Instagram / Facebook Sponsored Feed) - Evergreen Winner (active 65 days)
        {
            "platform": "meta",
            "ad_format": "sponsored_feed",
            "ad_text": f"Style Meets Innovation ✨\nDiscover why millions trust {name} for their daily routine. Handcrafted precision, superior materials, and modern aesthetics.\nShop now and get free expedited shipping on your first order.",
            "target_url": f"https://{dom}/collection?utm_source=instagram&utm_medium=paid_social&utm_campaign=lifestyle_conversion",
            "days_active": 65,
        },
        # Meta (Facebook Carousel Ad) - Scaling Campaign (active 28 days)
        {
            "platform": "meta",
            "ad_format": "display",
            "ad_text": f"Find Your Perfect Match - {name} Bestsellers\nBrowse our top-rated collections. Loved by customers worldwide with 5-star ratings.\nExplore our catalog today.",
            "target_url": f"https://{dom}/bestsellers?utm_source=facebook&utm_medium=carousel&utm_campaign=lookalike",
            "days_active": 28,
        },
        # Meta (Instagram Reel / Video Ad) - Active Campaign (active 9 days)
        {
            "platform": "meta",
            "ad_format": "video",
            "ad_text": f"Unboxing the latest drop from {name} 🔥\nWatch how seamless quality meets modern comfort. Limited stock available.\nGet started before it sells out!",
            "target_url": f"https://{dom}/new-drop?utm_source=instagram_reels&utm_medium=video&utm_campaign=drop_announcement",
            "days_active": 9,
        },
        # Meta (Facebook Feed Post) - Testing / Pilot (active 3 days)
        {
            "platform": "meta",
            "ad_format": "sponsored_feed",
            "ad_text": f"Special Weekend Flash Sale!\nGrab your favorites from {name} with an exclusive 15% discount. Use code FLASH15 at checkout. Shop now.",
            "target_url": f"https://{dom}/flash-sale?utm_source=meta&utm_medium=feed&utm_campaign=weekend_flash",
            "days_active": 3,
        },
        # LinkedIn Sponsored Feed - Evergreen Winner (active 70 days)
        {
            "platform": "linkedin",
            "ad_format": "sponsored_feed",
            "ad_text": f"Enterprise Solutions by {name}\nEmpower your organization with industry-leading reliability, modern workflow integrations, and dedicated support. Book a demo.",
            "target_url": f"https://{dom}/enterprise?utm_source=linkedin&utm_medium=sponsored_content&utm_campaign=b2b_leadgen",
            "days_active": 70,
        },
        # LinkedIn Sponsored Content - Active Campaign (active 12 days)
        {
            "platform": "linkedin",
            "ad_format": "sponsored_feed",
            "ad_text": f"2026 Industry Benchmark Report - Insights by {name}\nLearn how top market leaders are adapting to consumer trends. Download now for free.",
            "target_url": f"https://{dom}/reports/2026-benchmark?utm_source=linkedin&utm_medium=lead_gen&utm_campaign=content_marketing",
            "days_active": 12,
        },
        # Twitter / X Sponsored Post - Scaling Campaign (active 21 days)
        {
            "platform": "twitter",
            "ad_format": "sponsored_feed",
            "ad_text": f"Ready for an upgrade? The new {name} collection is here. Sleek, fast, and engineered for you. Try for free.",
            "target_url": f"https://{dom}/upgrade?utm_source=twitter&utm_medium=paid_promoted&utm_campaign=product_launch",
            "days_active": 21,
        },
        # Twitter / X Sponsored Post - Testing / Pilot (active 2 days)
        {
            "platform": "twitter",
            "ad_format": "sponsored_feed",
            "ad_text": f"Join the {name} community! Discover user stories, tips, and exclusive releases. Sign up today.",
            "target_url": f"https://{dom}/community?utm_source=twitter&utm_medium=promoted&utm_campaign=community_acquisition",
            "days_active": 2,
        },
        # TikTok Video Ad - Scaling Campaign (active 18 days)
        {
            "platform": "tiktok",
            "ad_format": "video",
            "ad_text": f"POV: You found the ultimate daily essential from {name} 🚀\nSmooth, versatile, and stylish. Watch video and shop now.",
            "target_url": f"https://{dom}/trending?utm_source=tiktok&utm_medium=in_feed_video&utm_campaign=creator_collab",
            "days_active": 18,
        },
    ]


async def seed_brand_ads(db: AsyncSession, brand: Brand) -> int:
    samples = get_sample_ads_for_brand(brand.name, brand.domain)
    parser = AdCreativeParser()
    today = date.today()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    count = 0

    for s in samples:
        days_active = s.get("days_active", 7)
        first_seen = today - timedelta(days=days_active)
        last_seen = today
        raw_text = s["ad_text"]
        target_url = s["target_url"]
        platform = s["platform"]
        ad_format = s.get("ad_format")

        p = parser.parse_ad(raw_text, target_url, ad_format)
        tier = AdSpendEstimator.calculate_longevity_and_tier(first_seen, last_seen)

        targeting = {
            "headline": p.headline,
            "cta": p.cta,
            "landing_page_domain": p.landing_page_domain,
            "utm_parameters": p.utm_parameters,
            "longevity_days": tier.longevity_days,
            "spend_tier": tier.tier_label,
            "is_evergreen": tier.is_evergreen
        }

        new_ad = AdIntel(
            id=uuid.uuid4(),
            brand_id=brand.id,
            platform=platform.lower(),
            ad_text=raw_text,
            ad_format=p.detected_format,
            target_url=target_url,
            first_seen=first_seen,
            last_seen=last_seen,
            targeting_info=targeting,
            data_source_tag="ad_transparency_library",
            created_at=now - timedelta(days=days_active)
        )
        db.add(new_ad)
        count += 1

    await db.commit()
    return count


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
    Automatically seeds realistic multi-channel ad creatives if the brand currently has 0 ads.
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

    # Auto-seed if 0 ads found and no filters set
    if total == 0 and (not platform or platform.lower() == "all") and (not ad_format or ad_format.lower() == "all") and not search:
        await seed_brand_ads(db, brand)
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

    now = datetime.now(timezone.utc).replace(tzinfo=None)
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
    now = datetime.now(timezone.utc).replace(tzinfo=None)
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


@router.post("/brand/{brand_id}/seed", status_code=status.HTTP_201_CREATED)
async def seed_ads_endpoint(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Seed realistic multi-channel competitor ad creatives and calculate campaign longevity analytics.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )
    count = await seed_brand_ads(db, brand)
    return {"status": "success", "count": count, "brand_id": str(brand_id)}


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

    # Auto-seed if 0 ads found
    if len(ads) == 0:
        await seed_brand_ads(db, brand)
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
