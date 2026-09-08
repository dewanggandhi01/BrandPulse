from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.brand import Brand
from app.models.mention import Mention
from app.models.sentiment import Sentiment
from app.schemas.sentiment import (
    MentionCreate,
    MentionBatchCreate,
    MentionRead,
    MentionListResponse,
    ReputationAnalyticsResponse,
    SourceStat,
    TopicStat,
    AnalyzeTextRequest,
    AnalyzeTextResponse
)
from workers.sentiment.analyzer import SentimentAnalyzer

logger = structlog.get_logger()
router = APIRouter()

@router.post("/analyze-text", response_model=AnalyzeTextResponse)
async def analyze_text_sentiment(payload: AnalyzeTextRequest) -> AnalyzeTextResponse:
    """
    Evaluate ad-hoc text sentiment immediately without persisting to database.
    """
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze_text(payload.text)
    return AnalyzeTextResponse(
        text=payload.text,
        label=res.label,
        positive_score=res.positive_score,
        negative_score=res.negative_score,
        neutral_score=res.neutral_score,
        compound_score=res.compound_score,
        model_version=res.model_version
    )

def get_sample_mentions(brand_name: str, brand_domain: str | None = None) -> list[dict]:
    name = brand_name
    dom = brand_domain or f"{name.lower().replace(' ', '')}.com"

    return [
        # Twitter / X
        {
            "source": "twitter",
            "source_url": f"https://x.com/tech_reviewer/status/1892019",
            "author": "@tech_reviewer",
            "content": f"The customer support from {name} was superb and fast! Resolved my issue within minutes. Highly recommend their service! 👍",
            "days_ago": 1,
        },
        {
            "source": "twitter",
            "source_url": f"https://x.com/sarah_runs/status/1892020",
            "author": "@sarah_runs",
            "content": f"Loving the new design and premium quality from {name}. Best purchase I have made all year, absolutely fantastic! 🔥",
            "days_ago": 2,
        },
        {
            "source": "twitter",
            "source_url": f"https://x.com/disappointed_dev/status/1892021",
            "author": "@disappointed_dev",
            "content": f"Terrible experience with {name}'s shipping delay. Overpriced items and frustrating customer service when asking for status. 😠",
            "days_ago": 3,
        },
        {
            "source": "twitter",
            "source_url": f"https://x.com/alex_m/status/1892022",
            "author": "@alex_m",
            "content": f"Does anyone know if {name} is releasing a new version next quarter? Wondering if I should wait before ordering.",
            "days_ago": 5,
        },
        {
            "source": "twitter",
            "source_url": f"https://x.com/daily_trends/status/1892023",
            "author": "@daily_trends",
            "content": f"Outstanding performance and top-tier reliability. {name} really knocked it out of the park with their latest update! 🚀",
            "days_ago": 6,
        },
        {
            "source": "twitter",
            "source_url": f"https://x.com/cautious_buyer/status/1892024",
            "author": "@cautious_buyer",
            "content": f"The mobile app for {name} is buggy and clunky after the latest patch. Please fix the login crash! 🤦",
            "days_ago": 8,
        },
        # Reddit
        {
            "source": "reddit",
            "source_url": f"https://reddit.com/r/reviews/comments/{name.lower()}_honest_review",
            "author": "u/HonestConsumer99",
            "content": f"In-depth 30-day review of {name}: The build quality and user experience are solid. Pricing plan is fair, though refund policy could be clearer. Overall very satisfied with the product quality.",
            "days_ago": 4,
        },
        {
            "source": "reddit",
            "source_url": f"https://reddit.com/r/technology/comments/{name.lower()}_discussion",
            "author": "u/TechGuru2026",
            "content": f"Comparing {name} with other top brands in this category. The feature set is intuitive, clean interface, and seamless API integration.",
            "days_ago": 7,
        },
        {
            "source": "reddit",
            "source_url": f"https://reddit.com/r/complaints/comments/{name.lower()}_billing",
            "author": "u/FrustratedShopper",
            "content": f"Avoid {name} if you care about quick refund policy. Subpar communication and slow support response over email.",
            "days_ago": 10,
        },
        {
            "source": "reddit",
            "source_url": f"https://reddit.com/r/gadgets/comments/{name.lower()}_impressions",
            "author": "u/GadgetFanatic",
            "content": f"First impressions of {name}: Super smooth onboarding and impressive speed. Really happy with the reliability so far.",
            "days_ago": 12,
        },
        # G2
        {
            "source": "g2",
            "source_url": f"https://g2.com/products/{name.lower()}/reviews/1",
            "author": "Marcus V., Enterprise Lead",
            "content": f"A true gamechanger for our team! {name} delivers excellent efficiency and reliable performance across the board. Highly recommended!",
            "days_ago": 9,
        },
        {
            "source": "g2",
            "source_url": f"https://g2.com/products/{name.lower()}/reviews/2",
            "author": "Elena K., Product Specialist",
            "content": f"Good product with lots of potential, but documentation could use improvement. Some confusing steps during initial setup.",
            "days_ago": 14,
        },
        {
            "source": "g2",
            "source_url": f"https://g2.com/products/{name.lower()}/reviews/3",
            "author": "David S., Operations Director",
            "content": f"Flawless integration with existing workflow. Powerful analytics and beautiful dashboard. {name} has saved us countless hours.",
            "days_ago": 16,
        },
        # Trustpilot
        {
            "source": "trustpilot",
            "source_url": f"https://trustpilot.com/review/{dom}",
            "author": "Chloe Bennett",
            "content": f"Five stars! Ordered from {name} last week, delivered in 2 days. Beautiful packaging, superb craftsmanship, and awesome quality. 💯",
            "days_ago": 3,
        },
        {
            "source": "trustpilot",
            "source_url": f"https://trustpilot.com/review/{dom}/2",
            "author": "Robert Miller",
            "content": f"Disappointed. The product arrived late and packaging was damaged. Unhelpful support when I asked for a replacement.",
            "days_ago": 11,
        },
        {
            "source": "trustpilot",
            "source_url": f"https://trustpilot.com/review/{dom}/3",
            "author": "Jessica Taylor",
            "content": f"Affordable price and great value for everyday use. Smooth ordering process on their website. Will definitely purchase again.",
            "days_ago": 15,
        },
        # News
        {
            "source": "news",
            "source_url": f"https://techcrunch.com/2026/09/{name.lower()}-growth-report",
            "author": "TechCrunch Editorial",
            "content": f"{name} demonstrates strong customer satisfaction and innovative product launches in its latest quarterly market evaluation.",
            "days_ago": 5,
        },
        {
            "source": "news",
            "source_url": f"https://forbes.com/sites/retail/{name.lower()}-competitive-edge",
            "author": "Forbes Brand Insights",
            "content": f"Industry analysis reveals {name} continues to gain market share through exceptional user experience and competitive pricing plan.",
            "days_ago": 18,
        },
        # Web
        {
            "source": "web",
            "source_url": f"https://forums.hardwarezone.com/threads/{name.lower()}-feedback",
            "author": "CyberKnight",
            "content": f"Has anyone tested {name} under heavy daily usage? Wondering about long term durability compared to alternatives.",
            "days_ago": 13,
        },
        {
            "source": "web",
            "source_url": f"https://discussions.apple.com/thread/{name.lower()}-compatible",
            "author": "PixelCrafter",
            "content": f"Awesome synergy and perfect compatibility with our setup. Brilliant execution by the {name} engineering team!",
            "days_ago": 20,
        },
    ]


async def seed_brand_mentions(db: AsyncSession, brand: Brand) -> int:
    samples = get_sample_mentions(brand.name, brand.domain)
    analyzer = SentimentAnalyzer()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    count = 0
    for s in samples:
        pub_date = now_naive - timedelta(days=s.get("days_ago", 1))
        sent_res = analyzer.analyze_text(s["content"])
        m_id = uuid.uuid4()

        m = Mention(
            id=m_id,
            brand_id=brand.id,
            source=s["source"].lower(),
            source_url=s["source_url"],
            content=s["content"],
            author=s["author"],
            published_at=pub_date,
            created_at=pub_date
        )
        db.add(m)

        sent = Sentiment(
            id=uuid.uuid4(),
            mention_id=m_id,
            label=sent_res.label,
            positive_score=sent_res.positive_score,
            negative_score=sent_res.negative_score,
            neutral_score=sent_res.neutral_score,
            model_version=sent_res.model_version,
            created_at=pub_date
        )
        db.add(sent)
        count += 1

    await db.commit()
    return count


@router.get("/brand/{brand_id}", response_model=MentionListResponse)
async def get_brand_mentions(
    brand_id: uuid.UUID,
    source: str | None = Query(None, description="Filter by source platform"),
    label: str | None = Query(None, description="Filter by sentiment label: positive, negative, neutral"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> MentionListResponse:
    """
    List brand mentions with optional source and sentiment filtering, with pagination.
    Automatically seeds realistic multi-channel mentions if the brand currently has 0 mentions.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Base query
    query = (
        select(Mention)
        .options(selectinload(Mention.sentiment))
        .where(Mention.brand_id == brand_id)
    )

    if source:
        query = query.where(Mention.source == source.lower())

    if label:
        query = query.join(Sentiment, Mention.id == Sentiment.mention_id).where(
            Sentiment.label == label.lower()
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Auto-seed if brand has 0 mentions and no filters were set
    if total == 0 and not source and not label:
        await seed_brand_mentions(db, brand)
        total = (await db.execute(count_query)).scalar_one()

    # Pagination and order
    query = query.order_by(desc(Mention.created_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    pages = (total + size - 1) // size if size > 0 else 1

    return MentionListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/brand/{brand_id}", response_model=MentionRead, status_code=status.HTTP_201_CREATED)
async def create_brand_mention(
    brand_id: uuid.UUID,
    payload: MentionCreate,
    db: AsyncSession = Depends(get_db)
) -> MentionRead:
    """
    Ingest a new mention, automatically evaluate its sentiment via SentimentAnalyzer,
    and persist both Mention and Sentiment records.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    analyzer = SentimentAnalyzer()
    sent_res = analyzer.analyze_text(payload.content)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    pub_date = payload.published_at.replace(tzinfo=None) if payload.published_at else now
    new_mention = Mention(
        id=uuid.uuid4(),
        brand_id=brand_id,
        source=payload.source.lower(),
        source_url=payload.source_url,
        content=payload.content,
        author=payload.author,
        published_at=pub_date,
        created_at=now
    )
    db.add(new_mention)

    sentiment_row = Sentiment(
        id=uuid.uuid4(),
        mention_id=new_mention.id,
        label=sent_res.label,
        positive_score=sent_res.positive_score,
        negative_score=sent_res.negative_score,
        neutral_score=sent_res.neutral_score,
        model_version=sent_res.model_version,
        created_at=now
    )
    db.add(sentiment_row)
    await db.commit()

    # Assign relation for response serialization
    new_mention.sentiment = sentiment_row
    return new_mention


@router.post("/brand/{brand_id}/batch", status_code=status.HTTP_201_CREATED)
async def batch_ingest_mentions(
    brand_id: uuid.UUID,
    payload: MentionBatchCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Batch ingest mentions, analyze and store all in a single transaction.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    analyzer = SentimentAnalyzer()
    created_count = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for item in payload.mentions:
        pub_date = item.published_at.replace(tzinfo=None) if item.published_at else now
        sent_res = analyzer.analyze_text(item.content)
        m_id = uuid.uuid4()
        m = Mention(
            id=m_id,
            brand_id=brand_id,
            source=item.source.lower(),
            source_url=item.source_url,
            content=item.content,
            author=item.author,
            published_at=pub_date,
            created_at=now
        )
        db.add(m)
        s = Sentiment(
            id=uuid.uuid4(),
            mention_id=m_id,
            label=sent_res.label,
            positive_score=sent_res.positive_score,
            negative_score=sent_res.negative_score,
            neutral_score=sent_res.neutral_score,
            model_version=sent_res.model_version,
            created_at=now
        )
        db.add(s)
        created_count += 1

    await db.commit()
    return {"status": "success", "count": created_count, "brand_id": brand_id}


@router.post("/brand/{brand_id}/seed", status_code=status.HTTP_201_CREATED)
async def seed_mentions_endpoint(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Seed realistic multi-channel mentions and calculate sentiment NLP for a brand.
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )
    count = await seed_brand_mentions(db, brand)
    return {"status": "success", "count": count, "brand_id": str(brand_id)}


@router.get("/brand/{brand_id}/analytics", response_model=ReputationAnalyticsResponse)
async def get_reputation_analytics(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> ReputationAnalyticsResponse:
    """
    Calculate high-level reputation analytics, including:
    - Net Sentiment Score (NSS: -100 to +100)
    - Positive / Negative / Neutral breakdown
    - Breakdown per platform/source
    - Top perception keywords and topics
    """
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Fetch all mentions with sentiment
    stmt = (
        select(Mention)
        .options(selectinload(Mention.sentiment))
        .where(Mention.brand_id == brand_id)
    )
    result = await db.execute(stmt)
    mentions = result.scalars().all()

    # Auto-seed if 0 mentions
    if len(mentions) == 0:
        await seed_brand_mentions(db, brand)
        result = await db.execute(stmt)
        mentions = result.scalars().all()

    total = len(mentions)
    if total == 0:
        return ReputationAnalyticsResponse(
            brand_id=brand_id,
            total_mentions=0,
            net_sentiment_score=0.0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            positive_pct=0.0,
            negative_pct=0.0,
            neutral_pct=0.0,
            sources_breakdown=[],
            top_topics=[]
        )

    pos_count = 0
    neg_count = 0
    neu_count = 0
    all_texts = []
    source_buckets: dict[str, dict] = {}

    for m in mentions:
        all_texts.append(m.content)
        lbl = m.sentiment.label if m.sentiment else "neutral"
        comp = 0.0
        if m.sentiment:
            comp = m.sentiment.positive_score - m.sentiment.negative_score

        if lbl == "positive":
            pos_count += 1
        elif lbl == "negative":
            neg_count += 1
        else:
            neu_count += 1

        src = m.source or "web"
        if src not in source_buckets:
            source_buckets[src] = {"count": 0, "positive": 0, "negative": 0, "neutral": 0, "compounds": []}
        source_buckets[src]["count"] += 1
        source_buckets[src][lbl] += 1
        source_buckets[src]["compounds"].append(comp)

    pos_pct = round((pos_count / total) * 100, 1)
    neg_pct = round((neg_count / total) * 100, 1)
    neu_pct = max(0.0, round(100.0 - pos_pct - neg_pct, 1))

    analyzer = SentimentAnalyzer()
    nss = analyzer.calculate_net_sentiment_score(pos_count, neg_count, total)

    # Build source breakdown
    sources_breakdown = []
    for src, data in source_buckets.items():
        avg_c = sum(data["compounds"]) / len(data["compounds"]) if data["compounds"] else 0.0
        sources_breakdown.append(SourceStat(
            source=src,
            count=data["count"],
            positive=data["positive"],
            negative=data["negative"],
            neutral=data["neutral"],
            avg_compound=round(avg_c, 3)
        ))

    # Build perception topics
    topics_raw = analyzer.extract_topics_and_perception(all_texts, top_n=8)
    top_topics = [
        TopicStat(
            topic=t.topic,
            frequency=t.frequency,
            sentiment_label=t.sentiment_label,
            average_compound=t.average_compound
        )
        for t in topics_raw
    ]

    return ReputationAnalyticsResponse(
        brand_id=brand_id,
        total_mentions=total,
        net_sentiment_score=nss,
        positive_count=pos_count,
        negative_count=neg_count,
        neutral_count=neu_count,
        positive_pct=pos_pct,
        negative_pct=neg_pct,
        neutral_pct=neu_pct,
        sources_breakdown=sources_breakdown,
        top_topics=top_topics
    )
