from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.brand import Brand, BrandUrl
from app.models.competitor import Competitor
from app.models.report import Report
from app.models.snapshot import Snapshot
from app.models.seo_audit import SeoAudit
from app.models.product import Product
from app.models.change_event import ChangeEvent
from app.models.mention import Mention
from app.models.ad_intel import AdIntel
from app.schemas.report import (
    ReportCreate,
    ReportRead,
    ReportListResponse,
    GenerateReportResponse
)
from workers.reports.generator import ExecutiveReportGenerator
from workers.ads.estimator import AdSpendEstimator
from workers.sentiment.analyzer import SentimentAnalyzer

logger = structlog.get_logger()
router = APIRouter()

async def compile_executive_brief_for_brand(
    db: AsyncSession,
    brand: Brand,
    report_type: str = "executive_brief"
) -> Report:
    """
    Synthesizes real-time intelligence across SEO, Pricing, Web Changes,
    Sentiment NSS, and Ad Spend Velocity into a persisted executive brief.
    """
    brand_id = brand.id

    # 1. Fetch latest SEO audit for brand
    seo_stmt = (
        select(SeoAudit)
        .join(Snapshot, SeoAudit.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .order_by(desc(SeoAudit.audited_at))
        .limit(1)
    )
    seo_exec = await db.execute(seo_stmt)
    latest_seo = seo_exec.scalar_one_or_none()
    seo_data = {
        "total_score": latest_seo.total_score if latest_seo else 70,
        "issues": latest_seo.issues if latest_seo else {}
    }

    # 2. Fetch products summary
    prod_stmt = select(Product).where(Product.brand_id == brand_id)
    prod_exec = await db.execute(prod_stmt)
    products = prod_exec.scalars().all()
    in_stock = sum(1 for p in products if p.availability != "out_of_stock")
    product_data = {
        "total_products": len(products),
        "in_stock_count": in_stock
    }

    # 3. Fetch change events count
    chg_stmt = (
        select(ChangeEvent)
        .join(Snapshot, ChangeEvent.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
    )
    chg_exec = await db.execute(chg_stmt)
    changes = chg_exec.scalars().all()
    change_data = {
        "total_changes": len(changes)
    }

    # 4. Fetch sentiment & mentions
    ment_stmt = (
        select(Mention)
        .options(selectinload(Mention.sentiment))
        .where(Mention.brand_id == brand_id)
    )
    ment_exec = await db.execute(ment_stmt)
    mentions = ment_exec.scalars().all()
    pos_count = sum(1 for m in mentions if m.sentiment and m.sentiment.label == "positive")
    neg_count = sum(1 for m in mentions if m.sentiment and m.sentiment.label == "negative")
    nss = SentimentAnalyzer.calculate_net_sentiment_score(pos_count, neg_count, len(mentions))
    sentiment_data = {
        "net_sentiment_score": nss,
        "total_mentions": len(mentions)
    }

    # 5. Fetch ads
    ad_stmt = select(AdIntel).where(AdIntel.brand_id == brand_id)
    ad_exec = await db.execute(ad_stmt)
    ads = ad_exec.scalars().all()
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
    ad_analytics = AdSpendEstimator.aggregate_brand_ad_intelligence(raw_ads)

    # 6. Fetch competitors count
    comp_stmt = select(func.count()).select_from(Competitor).where(Competitor.brand_id == brand_id)
    comp_count = (await db.execute(comp_stmt)).scalar_one() or 0

    # 7. Generate brief via engine
    generator = ExecutiveReportGenerator()
    brief = generator.generate_brief(
        brand_name=brand.name,
        brand_domain=brand.domain or f"{brand.name.lower()}.com",
        seo_data=seo_data,
        product_data=product_data,
        change_data=change_data,
        sentiment_data=sentiment_data,
        ad_data=ad_analytics,
        competitor_count=comp_count
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    report_row = Report(
        id=uuid.uuid4(),
        brand_id=brand_id,
        report_type=report_type,
        content={
            "health_score": brief.health_score,
            "risk_level": brief.risk_level,
            "pillar_scores": brief.pillar_scores,
            "kpi_highlights": brief.kpi_highlights,
            "swot": brief.swot,
            "recommendations": brief.recommendations
        },
        ai_narrative=brief.ai_narrative,
        generated_at=now,
        created_at=now
    )
    db.add(report_row)
    await db.commit()
    await db.refresh(report_row)
    return report_row

@router.post("/brand/{brand_id}/generate", response_model=GenerateReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_executive_report(
    brand_id: uuid.UUID,
    payload: ReportCreate = ReportCreate(),
    db: AsyncSession = Depends(get_db)
) -> GenerateReportResponse:
    """
    Synthesize multi-source intelligence across SEO, Pricing, Changes, Sentiment,
    and Ads to compile and persist an Executive Brief.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    report_row = await compile_executive_brief_for_brand(db, brand, payload.report_type)

    return GenerateReportResponse(
        message="Executive intelligence brief compiled successfully",
        report=report_row
    )

@router.post("/brand/{brand_id}/seed", response_model=GenerateReportResponse, status_code=status.HTTP_201_CREATED)
async def seed_report_endpoint(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> GenerateReportResponse:
    """
    On-demand seeding or re-synthesis of an executive brief for a brand.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    report_row = await compile_executive_brief_for_brand(db, brand, "executive_brief")

    return GenerateReportResponse(
        message="Executive intelligence brief compiled successfully",
        report=report_row
    )

@router.get("/brand/{brand_id}", response_model=ReportListResponse)
async def list_brand_reports(
    brand_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> ReportListResponse:
    """
    List all generated historical executive reports for a brand.
    Auto-synthesizes an initial baseline report if 0 reports exist.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    query = select(Report).where(Report.brand_id == brand_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Auto-generate baseline executive brief if 0 exist
    if total == 0:
        await compile_executive_brief_for_brand(db, brand, "executive_brief")
        total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(desc(Report.generated_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    reports = result.scalars().all()

    pages = (total + size - 1) // size if size > 0 else 1

    return ReportListResponse(
        items=reports,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{report_id}", response_model=ReportRead)
async def get_report_detail(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> ReportRead:
    """
    Retrieve full details of a specific executive report.
    """
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    return report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove an archived report from the repository.
    """
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    await db.delete(report)
    await db.commit()
