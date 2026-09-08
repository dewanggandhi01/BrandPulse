from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import structlog
from sqlalchemy import select, func

from workers.celery_app import app
from workers.extraction.product_extractor import ProductExtractor
from app.database import async_session_maker
from app.models.snapshot import Snapshot
from app.models.brand import BrandUrl
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.change_event import ChangeEvent

logger = structlog.get_logger()

async def _async_process_products(snapshot_id_str: str, brand_id_str: Optional[str] = None) -> Dict[str, Any]:
    snapshot_id = UUID(snapshot_id_str)
    logger.info("Processing products for snapshot", snapshot_id=str(snapshot_id))

    async with async_session_maker() as session:
        snapshot = await session.get(Snapshot, snapshot_id)
        if not snapshot:
            logger.error("Snapshot not found", snapshot_id=str(snapshot_id))
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Resolve brand_id and URL
        brand_id: Optional[UUID] = UUID(brand_id_str) if brand_id_str else None
        target_url = ""
        if snapshot.brand_url_id:
            b_url = await session.get(BrandUrl, snapshot.brand_url_id)
            if b_url:
                target_url = b_url.url
                if not brand_id:
                    brand_id = b_url.brand_id

        if not brand_id:
            raise ValueError(f"Cannot resolve brand_id for snapshot {snapshot_id}")

        html = snapshot.html_path or ""
        extracted = ProductExtractor.extract(html, target_url)
        logger.info("Extracted product candidates", count=len(extracted), snapshot_id=str(snapshot_id))

        new_count = 0
        updated_count = 0
        price_change_count = 0

        for item in extracted:
            price = item.get("current_price")
            currency = item.get("currency") or "USD"
            name = item.get("name")
            sku = item.get("sku")
            availability = item.get("availability") or "InStock"
            image_url = item.get("image_url")
            attributes = item.get("attributes")
            tag = item.get("data_source_tag")

            if not name or price is None:
                continue

            # Entity Resolution: match existing product by SKU or normalized Name
            existing_product: Optional[Product] = None
            if sku:
                query_sku = select(Product).where(
                    Product.brand_id == brand_id,
                    Product.sku == sku
                ).limit(1)
                res = await session.execute(query_sku)
                existing_product = res.scalar_one_or_none()

            if not existing_product:
                query_name = select(Product).where(
                    Product.brand_id == brand_id,
                    func.lower(Product.name) == name.strip().lower()
                ).limit(1)
                res = await session.execute(query_name)
                existing_product = res.scalar_one_or_none()

            if existing_product:
                updated_count += 1
                old_price = existing_product.current_price
                old_avail = existing_product.availability

                # Price tracking & anomaly detection
                if old_price is not None and price != old_price:
                    price_change_count += 1
                    is_anomaly, pct_shift = ProductExtractor.detect_price_anomaly(old_price, price)
                    change_type = "price_anomaly" if is_anomaly else "price_update"

                    event = ChangeEvent(
                        id=uuid4(),
                        snapshot_id=snapshot.id,
                        previous_snapshot_id=existing_product.snapshot_id,
                        change_type=change_type,
                        similarity_ratio=float(round(1.0 - (pct_shift / 100.0), 4)) if pct_shift < 100 else 0.0,
                        diff_details={
                            "product_id": str(existing_product.id),
                            "product_name": existing_product.name,
                            "old_price": float(old_price),
                            "new_price": float(price),
                            "currency": currency,
                            "percentage_change": pct_shift,
                            "is_anomaly": is_anomaly
                        },
                        ai_summary=f"Price {'jumped' if price > old_price else 'dropped'} by {pct_shift}% from {old_price} to {price} {currency}."
                    )
                    session.add(event)

                    # Update product current price
                    existing_product.current_price = price
                    existing_product.currency = currency

                    # Record Price History entry
                    p_hist = PriceHistory(
                        id=uuid4(),
                        product_id=existing_product.id,
                        price=price,
                        currency=currency
                    )
                    session.add(p_hist)

                # Stock status change
                if old_avail != availability:
                    stock_event = ChangeEvent(
                        id=uuid4(),
                        snapshot_id=snapshot.id,
                        previous_snapshot_id=existing_product.snapshot_id,
                        change_type="stock_status_change",
                        similarity_ratio=1.0,
                        diff_details={
                            "product_id": str(existing_product.id),
                            "product_name": existing_product.name,
                            "old_status": old_avail,
                            "new_status": availability
                        },
                        ai_summary=f"Availability changed from {old_avail} to {availability}."
                    )
                    session.add(stock_event)
                    existing_product.availability = availability

                # Update metadata
                existing_product.snapshot_id = snapshot.id
                if image_url:
                    existing_product.image_url = image_url
                if attributes:
                    existing_product.attributes = attributes

            else:
                # Create brand new Product
                new_count += 1
                new_prod = Product(
                    id=uuid4(),
                    snapshot_id=snapshot.id,
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
                session.add(new_prod)
                await session.flush()  # populate new_prod.id

                # Initial PriceHistory entry
                p_hist = PriceHistory(
                    id=uuid4(),
                    product_id=new_prod.id,
                    price=price,
                    currency=currency
                )
                session.add(p_hist)

        await session.commit()

        logger.info(
            "Product extraction completed",
            snapshot_id=str(snapshot_id),
            brand_id=str(brand_id),
            total_extracted=len(extracted),
            new_products=new_count,
            updated_products=updated_count,
            price_changes=price_change_count
        )

        return {
            "snapshot_id": str(snapshot_id),
            "brand_id": str(brand_id),
            "extracted_count": len(extracted),
            "new_products": new_count,
            "updated_products": updated_count,
            "price_changes": price_change_count
        }

@app.task(name="workers.tasks.extraction.process_snapshot_products", bind=True)
def process_snapshot_products(self, snapshot_id: str, brand_id: Optional[str] = None) -> Dict[str, Any]:
    """Celery task to extract products and track price histories from snapshot."""
    try:
        return asyncio.run(_async_process_products(snapshot_id, brand_id))
    except Exception as exc:
        logger.error("Error processing snapshot products", snapshot_id=snapshot_id, error=str(exc))
        raise
