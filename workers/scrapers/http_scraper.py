from __future__ import annotations
import asyncio
import random
import time
import httpx
import logging
from typing import Any, Dict, Optional

from .base import BaseScraper, ScrapedResult
from .robots_parser import RobotsParser
from .rate_limiter import DomainRateLimiter

logger = logging.getLogger(__name__)

class HttpScraper(BaseScraper):
    """
    Tier 1 High-Performance Scraper using httpx.
    Implements:
    - robots.txt compliance validation
    - per-domain token bucket rate limiting
    - conditional HTTP headers (ETag / Last-Modified -> 304 Not Modified)
    - exponential backoff with jitter on HTTP 429 and 503
    - full provenance metadata capture
    """
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        enforce_robots: bool = True,
        rate_limiter: Optional[DomainRateLimiter] = None
    ):
        super().__init__(timeout=timeout, max_retries=max_retries, user_agent=user_agent)
        self.enforce_robots = enforce_robots
        self.robots = RobotsParser(timeout=10.0)
        self.rate_limiter = rate_limiter or DomainRateLimiter()

    async def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        **kwargs: Any
    ) -> ScrapedResult:
        start_time = time.perf_counter()

        # 1. robots.txt check
        if self.enforce_robots:
            allowed = await self.robots.can_fetch(url, self.user_agent)
            if not allowed:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.warning("Scrape disallowed by robots.txt: %s", url)
                return ScrapedResult(
                    url=url,
                    status_code=403,
                    html="",
                    error="Disallowed by robots.txt",
                    elapsed_ms=elapsed,
                    is_modified=False,
                    metadata={"blocked_by": "robots.txt"}
                )

            # Check crawl delay
            crawl_delay = await self.robots.get_crawl_delay(url, self.user_agent)
        else:
            crawl_delay = None

        # 2. Rate limiting backpressure
        await self.rate_limiter.acquire(url, custom_delay=crawl_delay)

        # 3. Prepare headers & conditional request
        headers = self.get_default_headers()
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        attempt = 0
        backoff_base = 1.0

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            while attempt < self.max_retries:
                attempt += 1
                try:
                    t0 = time.perf_counter()
                    resp = await client.get(url, headers=headers)
                    elapsed_ms = (time.perf_counter() - t0) * 1000

                    # 304 Not Modified
                    if resp.status_code == 304:
                        return ScrapedResult(
                            url=url,
                            status_code=304,
                            html="",
                            headers=dict(resp.headers),
                            is_modified=False,
                            elapsed_ms=elapsed_ms,
                            metadata={"tier": "http_tier1", "attempts": attempt}
                        )

                    # 429 or 503: retry with backoff + jitter
                    if resp.status_code in (429, 503):
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            wait = float(retry_after)
                        else:
                            wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)

                        logger.warning("HTTP %d for %s (attempt %d/%d). Backing off %.2fs",
                                       resp.status_code, url, attempt, self.max_retries, wait)
                        if attempt < self.max_retries:
                            await asyncio.sleep(wait)
                            continue

                    resp.raise_for_status()

                    return ScrapedResult(
                        url=str(resp.url),
                        status_code=resp.status_code,
                        html=resp.text,
                        headers=dict(resp.headers),
                        is_modified=True,
                        elapsed_ms=elapsed_ms,
                        metadata={"tier": "http_tier1", "attempts": attempt}
                    )

                except httpx.HTTPStatusError as err:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    if attempt >= self.max_retries:
                        return ScrapedResult(
                            url=url,
                            status_code=err.response.status_code,
                            html=err.response.text if err.response else "",
                            headers=dict(err.response.headers) if err.response else {},
                            error=f"HTTPStatusError: {err}",
                            elapsed_ms=elapsed_ms,
                            metadata={"tier": "http_tier1", "attempts": attempt}
                        )
                    await asyncio.sleep(backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.3))

                except (httpx.RequestError, asyncio.TimeoutError) as err:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    if attempt >= self.max_retries:
                        return ScrapedResult(
                            url=url,
                            status_code=504 if isinstance(err, asyncio.TimeoutError) else 502,
                            html="",
                            error=f"RequestError: {err}",
                            elapsed_ms=elapsed_ms,
                            metadata={"tier": "http_tier1", "attempts": attempt}
                        )
                    await asyncio.sleep(backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.3))

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return ScrapedResult(
            url=url,
            status_code=500,
            html="",
            error="Exceeded maximum retry attempts",
            elapsed_ms=elapsed_ms,
            metadata={"tier": "http_tier1", "attempts": attempt}
        )
