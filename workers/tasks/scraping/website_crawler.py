from __future__ import annotations
import asyncio
import hashlib
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from sqlalchemy import select, update
import structlog
from uuid import UUID

from workers.celery_app import app
from workers.scrapers import HttpScraper, BrowserScraper, ScrapedResult
from app.database import async_session_maker
from app.models.scrape_job import ScrapeJob
from app.models.snapshot import Snapshot
from app.models.brand import Brand, BrandUrl

logger = structlog.get_logger()

def extract_internal_links(html: str, base_url: str, max_links: int = 20) -> List[str]:
    """Extract valid internal HTTP/HTTPS links belonging to same domain."""
    if not html:
        return []
    base_netloc = urlparse(base_url).netloc
    soup = BeautifulSoup(html, "lxml")
    links: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.scheme in ("http", "https") and parsed.netloc == base_netloc:
            # Strip query params and fragments for crawl frontier
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            if clean_url and clean_url != base_url.rstrip("/"):
                links.add(clean_url)
                if len(links) >= max_links:
                    break

    return list(links)

async def _async_crawl(
    job_id_str: str,
    brand_id_str: str,
    seed_urls: List[str],
    max_depth: int = 1,
    max_pages: int = 10,
    tier: str = "auto"
) -> Dict[str, Any]:
    job_id = UUID(job_id_str)
    brand_id = UUID(brand_id_str)
    
    start_time = time.perf_counter()
    logger.info("Starting crawl job", job_id=str(job_id), brand_id=str(brand_id), seed_urls=seed_urls)

    http_scraper = HttpScraper()
    browser_scraper = BrowserScraper() if tier == "browser" else None

    crawled_count = 0
    failed_count = 0
    unchanged_count = 0
    snapshot_ids: List[str] = []

    async with async_session_maker() as session:
        # Mark job as running
        await session.execute(
            update(ScrapeJob)
            .where(ScrapeJob.id == job_id)
            .values(status="running", started_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        await session.commit()

        frontier: List[tuple[str, int]] = [(u, 0) for u in seed_urls]
        visited: set[str] = set()

        while frontier and crawled_count < max_pages:
            current_url, depth = frontier.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                # 1. Scrape URL
                if tier == "browser" and browser_scraper:
                    result: ScrapedResult = await browser_scraper.scrape(current_url)
                else:
                    result = await http_scraper.scrape(current_url)
                    # Dynamic Tier Escalation Protocol (09-data-scraping):
                    # If in auto mode and response is an empty client-side SPA shell or blocked (403/429/503), escalate to BrowserScraper
                    if tier == "auto" and (
                        (result.status_code == 200 and ("<div id=\"root\"></div>" in result.html or "<div id=\"app\"></div>" in result.html) and len(result.html.strip()) < 1500)
                        or result.status_code in (403, 429, 503)
                        or (not result.html and result.error)
                    ):
                        logger.info("Escalating to Tier 3 BrowserScraper", url=current_url, status=result.status_code)
                        if browser_scraper is None:
                            browser_scraper = BrowserScraper()
                        browser_res = await browser_scraper.scrape(current_url)
                        if browser_res.html or browser_res.status_code == 200:
                            result = browser_res

                if not result.html and (result.status_code >= 400 or result.error):
                    logger.warning("Scrape error (no content)", url=current_url, status=result.status_code, error=result.error)
                    failed_count += 1
                    continue

                crawled_count += 1

                # 2. Get or create BrandUrl entry
                stmt = select(BrandUrl).where(BrandUrl.brand_id == brand_id, BrandUrl.url == current_url)
                res = await session.execute(stmt)
                brand_url = res.scalar_one_or_none()

                if not brand_url:
                    brand_url = BrandUrl(
                        brand_id=brand_id,
                        url=current_url,
                        url_type="discovered" if depth > 0 else "seed",
                        is_active=True
                    )
                    session.add(brand_url)
                    await session.flush()

                # 3. Check for existing identical snapshot (Deduplication via MurmurHash/SHA-256)
                content_hash = result.content_hash or hashlib.sha256(result.html.encode("utf-8")).hexdigest()
                dup_stmt = select(Snapshot).where(
                    Snapshot.brand_url_id == brand_url.id,
                    Snapshot.content_hash == content_hash
                )
                dup_res = await session.execute(dup_stmt)
                existing_snap = dup_res.scalar_one_or_none()

                if existing_snap:
                    unchanged_count += 1
                    logger.info("Identical snapshot exists, skipping duplicate row", url=current_url)
                else:
                    clean_html = (result.html or "").replace("\x00", "")
                    # Create new snapshot
                    snapshot = Snapshot(
                        brand_url_id=brand_url.id,
                        scrape_job_id=job_id,
                        content_hash=content_hash,
                        html_size=len(clean_html.encode("utf-8")),
                        status_code=result.status_code,
                        headers=result.headers,
                        html_path=clean_html[:1000000] # store raw HTML content (bounded)
                    )
                    session.add(snapshot)
                    await session.flush()
                    snapshot_ids.append(str(snapshot.id))

                    # Auto-dispatch 4-pillar SEO audit task to Celery 'seo' queue
                    try:
                        from workers.tasks.seo.seo_auditor import audit_snapshot_seo
                        audit_snapshot_seo.apply_async(
                            kwargs={"snapshot_id": str(snapshot.id), "target_url": current_url},
                            queue="seo"
                        )
                    except Exception as seo_task_err:
                        logger.warning("Failed to auto-dispatch SEO audit task", error=str(seo_task_err))

                    # Auto-dispatch Product & Pricing extraction task
                    try:
                        from workers.tasks.extraction.product_processor import process_snapshot_products
                        process_snapshot_products.apply_async(
                            kwargs={"snapshot_id": str(snapshot.id), "brand_id": str(brand_id)},
                            queue="scraping"
                        )
                    except Exception as prod_task_err:
                        logger.warning("Failed to auto-dispatch product extraction task", error=str(prod_task_err))

                    # Auto-dispatch website change detection & diffing task
                    try:
                        from workers.tasks.diffing.diff_detector import detect_snapshot_changes
                        detect_snapshot_changes.apply_async(
                            kwargs={"snapshot_id": str(snapshot.id)},
                            queue="diffing"
                        )
                    except Exception as diff_task_err:
                        logger.warning("Failed to auto-dispatch diff task", error=str(diff_task_err))


                # 4. Discover new internal links if depth permits
                if depth < max_depth and crawled_count + len(frontier) < max_pages:
                    discovered = extract_internal_links(result.html, current_url, max_links=5)
                    for new_url in discovered:
                        if new_url not in visited and not any(u == new_url for u, _ in frontier):
                            frontier.append((new_url, depth + 1))

                # Periodic in-flight progress checkpoint
                if crawled_count % 2 == 0 or not frontier:
                    await session.execute(
                        update(ScrapeJob)
                        .where(ScrapeJob.id == job_id)
                        .values(
                            config={
                                "pages_crawled": crawled_count,
                                "pages_failed": failed_count,
                                "pages_unchanged": unchanged_count,
                                "snapshots_created": len(snapshot_ids),
                                "in_progress": True
                            }
                        )
                    )
                    await session.commit()

            except Exception as item_err:
                await session.rollback()
                failed_count += 1
                logger.exception("Unexpected error processing url", url=current_url, error=str(item_err))

        total_elapsed = (time.perf_counter() - start_time) * 1000

        # Mark job as completed and update stats
        stats = {
            "pages_crawled": crawled_count,
            "pages_failed": failed_count,
            "pages_unchanged": unchanged_count,
            "snapshots_created": len(snapshot_ids),
            "elapsed_ms": round(total_elapsed, 2)
        }

        await session.execute(
            update(ScrapeJob)
            .where(ScrapeJob.id == job_id)
            .values(
                status="completed" if crawled_count > 0 or failed_count == 0 else "failed",
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                config=stats
            )
        )
        await session.commit()

    logger.info("Crawl job finished", job_id=str(job_id), stats=stats)
    return {
        "job_id": str(job_id),
        "status": "completed",
        "snapshots": snapshot_ids,
        "stats": stats
    }

@app.task(name="workers.tasks.scraping.crawl_website", bind=True, max_retries=2)
def crawl_website(
    self,
    job_id: str,
    brand_id: str,
    seed_urls: List[str],
    max_depth: int = 1,
    max_pages: int = 10,
    tier: str = "auto"
) -> Dict[str, Any]:
    """
    Celery task orchestrating web crawling.
    Passes only lightweight identifiers (job_id, snapshot_ids) across the message bus.
    """
    try:
        return asyncio.run(_async_crawl(
            job_id_str=job_id,
            brand_id_str=brand_id,
            seed_urls=seed_urls,
            max_depth=max_depth,
            max_pages=max_pages,
            tier=tier
        ))
    except Exception as exc:
        logger.exception("Crawl task encountered fatal failure", job_id=job_id, exc=str(exc))
        # Update job status to failed in DB
        async def _fail_job():
            async with async_session_maker() as session:
                await session.execute(
                    update(ScrapeJob)
                    .where(ScrapeJob.id == UUID(job_id))
                    .values(
                        status="failed",
                        error_message=str(exc),
                        completed_at=datetime.now(timezone.utc).replace(tzinfo=None)
                    )
                )
                await session.commit()
        try:
            asyncio.run(_fail_job())
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=10)
