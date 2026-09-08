from __future__ import annotations
import uuid
from typing import Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc

from app.api.deps import get_db
from app.models.brand import Brand, BrandUrl
from app.models.snapshot import Snapshot
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.change_event import ChangeEvent
from app.schemas.product import (
    ProductRead,
    ProductDetailRead,
    PriceHistoryRead,
    ProductListResponse,
    ProductAnalyticsSummary
)
from workers.extraction.product_extractor import ProductExtractor

logger = structlog.get_logger()
router = APIRouter()

@router.post("/brands/{brand_id}/products/extract", status_code=201)
async def extract_brand_products(
    brand_id: uuid.UUID,
    snapshot_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Extracts products from the latest or specified crawled snapshot of a brand."""
    # 1. Verify Brand exists
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")

    # 2. Find target snapshots
    if snapshot_id:
        snapshot = await db.get(Snapshot, snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")
        brand_url_obj = await db.get(BrandUrl, snapshot.brand_url_id) if snapshot.brand_url_id else None
        rows = [(snapshot, brand_url_obj)]
    else:
        query = (
            select(Snapshot, BrandUrl)
            .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
            .where(BrandUrl.brand_id == brand_id)
            .order_by(Snapshot.captured_at.desc())
            .limit(25)
        )
        res = await db.execute(query)
        rows = list(res.all())

        if not rows and brand.domain:
            target = brand.domain.strip()
            if not target.startswith("http://") and not target.startswith("https://"):
                target = f"https://{target}"
            try:
                from workers.scrapers.http_scraper import HttpScraper
                scraper = HttpScraper(timeout=10.0, max_retries=1)
                scrap_res = await scraper.scrape(target)
                if scrap_res.status_code == 200 and scrap_res.html:
                    res_bu = await db.execute(
                        select(BrandUrl).where(BrandUrl.brand_id == brand_id).limit(1)
                    )
                    bu = res_bu.scalar_one_or_none()
                    if not bu:
                        bu = BrandUrl(
                            id=uuid.uuid4(),
                            brand_id=brand_id,
                            url=target,
                            url_type="canonical",
                            status="active"
                        )
                        db.add(bu)
                        await db.flush()
                    new_snap = Snapshot(
                        id=uuid.uuid4(),
                        brand_url_id=bu.id,
                        status_code=200,
                        content_hash=scrap_res.content_hash,
                        headers=scrap_res.headers,
                        html_path=scrap_res.html,
                        captured_at=datetime.now(timezone.utc)
                    )
                    db.add(new_snap)
                    await db.flush()
                    rows = [(new_snap, bu)]
            except Exception as exc:
                logger.warning("On-the-fly scrape fallback failed", error=str(exc))

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="No crawled snapshots found for this brand. Run a website crawl first."
            )

    # 3. Extract products across target snapshots
    all_extracted: list[dict[str, Any]] = []
    primary_snapshot_id = str(rows[0][0].id)

    for snap, b_url in rows:
        url_for_snap = b_url.url if b_url else (brand.domain or "")
        items = ProductExtractor.extract(snap.html_path or "", url_for_snap)
        for itm in items:
            itm["_snapshot_id"] = snap.id
            all_extracted.append(itm)

    # Deduplicate products in this batch by name and sku
    deduped_items: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for itm in all_extracted:
        k = f"{(itm.get('name') or '').strip().lower()}:::{(itm.get('sku') or '').strip().lower()}"
        if k not in seen_keys:
            seen_keys.add(k)
            deduped_items.append(itm)
    
    new_count = 0
    updated_count = 0
    price_changes = 0

    for item in deduped_items:
        price = item.get("current_price")
        name = item.get("name")
        sku = item.get("sku")
        currency = item.get("currency") or "USD"
        availability = item.get("availability") or "InStock"
        image_url = item.get("image_url")
        attributes = item.get("attributes")
        tag = item.get("data_source_tag")
        item_snap_id = item.get("_snapshot_id", rows[0][0].id)

        if not name or price is None:
            continue

        # Entity resolution: match by SKU or Name
        existing: Optional[Product] = None
        if sku:
            res_sku = await db.execute(
                select(Product).where(Product.brand_id == brand_id, Product.sku == sku).limit(1)
            )
            existing = res_sku.scalar_one_or_none()

        if not existing:
            res_name = await db.execute(
                select(Product).where(
                    Product.brand_id == brand_id,
                    func.lower(Product.name) == name.strip().lower()
                ).limit(1)
            )
            existing = res_name.scalar_one_or_none()

        if existing:
            updated_count += 1
            old_price = existing.current_price
            if old_price is not None and old_price != price:
                price_changes += 1
                is_anomaly, pct_shift = ProductExtractor.detect_price_anomaly(old_price, price)
                change_type = "price_anomaly" if is_anomaly else "price_update"

                event = ChangeEvent(
                    id=uuid.uuid4(),
                    snapshot_id=item_snap_id,
                    previous_snapshot_id=existing.snapshot_id,
                    change_type=change_type,
                    similarity_ratio=float(round(1.0 - (pct_shift / 100.0), 4)) if pct_shift < 100 else 0.0,
                    diff_details={
                        "product_id": str(existing.id),
                        "old_price": float(old_price),
                        "new_price": float(price),
                        "pct_shift": pct_shift
                    },
                    ai_summary=f"Price changed from {old_price} to {price} {currency} ({pct_shift}%)."
                )
                db.add(event)

                # Record price history
                p_hist = PriceHistory(
                    id=uuid.uuid4(),
                    product_id=existing.id,
                    price=price,
                    currency=currency
                )
                db.add(p_hist)

            existing.current_price = price
            existing.currency = currency
            existing.availability = availability
            existing.snapshot_id = item_snap_id
            if image_url:
                existing.image_url = image_url
            if attributes:
                existing.attributes = attributes
        else:
            new_count += 1
            new_p = Product(
                id=uuid.uuid4(),
                snapshot_id=item_snap_id,
                brand_id=brand_id,
                name=name,
                sku=sku,
                current_price=price,
                currency=currency,
                availability=availability,
                image_url=image_url,
                attributes=attributes,
                data_source_tag=tag
            )
            db.add(new_p)
            await db.flush()

            # Record initial price history
            p_hist = PriceHistory(
                id=uuid.uuid4(),
                product_id=new_p.id,
                price=price,
                currency=currency
            )
            db.add(p_hist)

    await db.commit()
    logger.info("Brand product extraction finished", brand_id=str(brand_id), extracted=len(deduped_items))

    return {
        "status": "completed",
        "snapshot_id": primary_snapshot_id,
        "total_extracted": len(deduped_items),
        "new_products": new_count,
        "updated_products": updated_count,
        "price_changes": price_changes
    }

@router.get("/brands/{brand_id}/products", response_model=ProductListResponse)
async def list_brand_products(
    brand_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    availability: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    order_by: str = Query("recent", enum=["recent", "price_asc", "price_desc", "name_asc"]),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists products belonging to a brand with search, filtering, and pagination."""
    query = select(Product).where(Product.brand_id == brand_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.where((Product.name.ilike(term)) | (Product.sku.ilike(term)))

    if availability:
        query = query.where(func.lower(Product.availability) == availability.lower())

    if min_price is not None:
        query = query.where(Product.current_price >= min_price)

    if max_price is not None:
        query = query.where(Product.current_price <= max_price)

    # Ordering
    if order_by == "price_asc":
        query = query.order_by(asc(Product.current_price))
    elif order_by == "price_desc":
        query = query.order_by(desc(Product.current_price))
    elif order_by == "name_asc":
        query = query.order_by(asc(Product.name))
    else:
        query = query.order_by(desc(Product.id))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    count_res = await db.execute(count_query)
    total = count_res.scalar() or 0

    # Paginate
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    res = await db.execute(query)
    items = list(res.scalars().all())

    pages = (total + size - 1) // size if total > 0 else 1

    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/products/{product_id}", response_model=ProductDetailRead)
async def get_product_detail(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetches a single product by ID along with its complete time-series price history."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    # Fetch price history ordered by captured_at ascending
    q_hist = select(PriceHistory).where(PriceHistory.product_id == product_id).order_by(asc(PriceHistory.captured_at))
    res_hist = await db.execute(q_hist)
    history = list(res_hist.scalars().all())

    return ProductDetailRead(
        id=product.id,
        snapshot_id=product.snapshot_id,
        brand_id=product.brand_id,
        name=product.name,
        sku=product.sku,
        current_price=product.current_price,
        currency=product.currency or "USD",
        availability=product.availability or "InStock",
        image_url=product.image_url,
        attributes=product.attributes,
        data_source_tag=product.data_source_tag,
        price_history=history
    )

@router.get("/brands/{brand_id}/products/analytics", response_model=ProductAnalyticsSummary)
async def get_brand_product_analytics(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Computes catalog analytics including min/max/avg price and in-stock counts."""
    # Aggregates
    agg_q = select(
        func.count(Product.id).label("total"),
        func.avg(Product.current_price).label("avg_price"),
        func.min(Product.current_price).label("min_price"),
        func.max(Product.current_price).label("max_price"),
    ).where(Product.brand_id == brand_id)

    res_agg = await db.execute(agg_q)
    row = res_agg.first()

    total = row[0] if row and row[0] is not None else 0
    avg_p = float(row[1]) if row and row[1] is not None else None
    min_p = float(row[2]) if row and row[2] is not None else None
    max_p = float(row[3]) if row and row[3] is not None else None

    # Count in stock
    stock_q = select(func.count(Product.id)).where(
        Product.brand_id == brand_id,
        func.lower(Product.availability).in_(["instock", "in_stock"])
    )
    stock_res = await db.execute(stock_q)
    in_stock = stock_res.scalar() or 0
    out_of_stock = max(0, total - in_stock)

    # Count price change events
    change_q = select(func.count(ChangeEvent.id)).join(
        Snapshot, ChangeEvent.snapshot_id == Snapshot.id
    ).join(
        BrandUrl, Snapshot.brand_url_id == BrandUrl.id
    ).where(
        BrandUrl.brand_id == brand_id,
        ChangeEvent.change_type.in_(["price_update", "price_anomaly"])
    )
    change_res = await db.execute(change_q)
    changes_count = change_res.scalar() or 0

    # Dominant currency
    curr_q = select(Product.currency).where(Product.brand_id == brand_id, Product.currency.isnot(None)).limit(1)
    curr_res = await db.execute(curr_q)
    dominant_currency = curr_res.scalar() or "USD"

    return ProductAnalyticsSummary(
        total_products=total,
        in_stock_count=in_stock,
        out_of_stock_count=out_of_stock,
        avg_price=round(avg_p, 2) if avg_p else None,
        min_price=round(min_p, 2) if min_p else None,
        max_price=round(max_p, 2) if max_p else None,
        currency=dominant_currency,
        price_changes_count=changes_count
    )
