from __future__ import annotations
import json
import asyncio
import time
import httpx
import logging
import random
from typing import Any, Dict, Optional

from .base import BaseScraper, ScrapedResult
from .rate_limiter import DomainRateLimiter

logger = logging.getLogger(__name__)


class ApiScraper(BaseScraper):
    """
    Tier 2 Direct API Scraper.
    Targeted for websites with internal REST/GraphQL endpoints discovered via network analysis.
    Direct JSON/GraphQL consumption bypasses DOM parsing overhead completely.
    """
    def __init__(
        self,
        timeout: float = 20.0,
        max_retries: int = 3,
        auth_token: Optional[str] = None,
        rate_limiter: Optional[DomainRateLimiter] = None,
        user_agent: Optional[str] = None,
        proxy_url: Optional[str] = None,
        proxy_pool: Optional[list[str]] = None,
    ):
        super().__init__(
            timeout=timeout,
            max_retries=max_retries,
            user_agent=user_agent,
            proxy_url=proxy_url,
            proxy_pool=proxy_pool,
        )
        self.auth_token = auth_token
        self.rate_limiter = rate_limiter or DomainRateLimiter()

    async def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> ScrapedResult:
        start_time = time.perf_counter()
        
        # 1. Rate limiting backpressure
        await self.rate_limiter.acquire(url)

        attempt = 0
        backoff_base = 1.0

        # Rotate UA/proxy per attempt
        req_headers = self.get_default_headers()
        req_headers["Accept"] = "application/json, text/plain, */*"

        if self.auth_token:
            req_headers["Authorization"] = f"Bearer {self.auth_token}"
        if headers:
            req_headers.update(headers)
        if etag:
            req_headers["If-None-Match"] = etag
        if last_modified:
            req_headers["If-Modified-Since"] = last_modified

        proxy_url = self.get_proxy()
        mounts = {"http://": httpx.AsyncHTTPTransport(proxy=proxy_url), "https://": httpx.AsyncHTTPTransport(proxy=proxy_url)} if proxy_url else None

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, mounts=mounts) as client:
            while attempt < self.max_retries:
                attempt += 1
                try:
                    t0 = time.perf_counter()
                    if method.upper() == "POST":
                        resp = await client.post(url, json=payload, headers=req_headers)
                    else:
                        resp = await client.get(url, params=payload, headers=req_headers)
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
                            metadata={"tier": "api_tier2", "attempts": attempt}
                        )

                    # 429 or 503: retry with backoff + jitter
                    if resp.status_code in (429, 503):
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            wait = float(retry_after)
                        else:
                            wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)

                        logger.warning(
                            "API scrape HTTP %d for %s (attempt %d/%d). Backing off %.2fs",
                            resp.status_code, url, attempt, self.max_retries, wait
                        )
                        if attempt < self.max_retries:
                            await asyncio.sleep(wait)
                            continue

                    resp.raise_for_status()
                    data_text = resp.text

                    # Parse JSON to verify integrity
                    try:
                        data_json = resp.json()
                        metadata = {
                            "tier": "api_tier2",
                            "is_json": True,
                            "attempts": attempt,
                            "keys": list(data_json.keys()) if isinstance(data_json, dict) else len(data_json)
                        }
                    except Exception:
                        metadata = {"tier": "api_tier2", "is_json": False, "attempts": attempt}

                    if proxy_url:
                        metadata["proxy_used"] = True

                    return ScrapedResult(
                        url=str(resp.url),
                        status_code=resp.status_code,
                        html=data_text,
                        headers=dict(resp.headers),
                        is_modified=True,
                        elapsed_ms=elapsed_ms,
                        metadata=metadata
                    )

                except httpx.HTTPStatusError as err:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    if attempt >= self.max_retries:
                        return ScrapedResult(
                            url=url,
                            status_code=err.response.status_code if err.response else 500,
                            html=err.response.text if err.response else "",
                            headers=dict(err.response.headers) if err.response else {},
                            error=f"HTTPStatusError: {err}",
                            elapsed_ms=elapsed_ms,
                            metadata={"tier": "api_tier2", "attempts": attempt}
                        )
                    wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.3)
                    await asyncio.sleep(wait)

                except (httpx.RequestError, asyncio.TimeoutError) as err:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    if attempt >= self.max_retries:
                        return ScrapedResult(
                            url=url,
                            status_code=504 if isinstance(err, asyncio.TimeoutError) else 502,
                            html="",
                            error=f"RequestError: {err}",
                            elapsed_ms=elapsed_ms,
                            metadata={"tier": "api_tier2", "attempts": attempt}
                        )
                    wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.3)
                    await asyncio.sleep(wait)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return ScrapedResult(
            url=url,
            status_code=500,
            html="",
            error="Exceeded maximum retry attempts",
            elapsed_ms=elapsed_ms,
            metadata={"tier": "api_tier2", "attempts": attempt}
        )
