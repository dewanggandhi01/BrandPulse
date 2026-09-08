from __future__ import annotations
import asyncio
import random
import time
import logging
from typing import Any, Dict, Optional

from .base import BaseScraper, ScrapedResult
from .rate_limiter import DomainRateLimiter

logger = logging.getLogger(__name__)


class BrowserScraper(BaseScraper):
    """
    Tier 3 Playwright Headless Browser Scraper.
    Escalation only: Used when SPA hydration, client-side JavaScript execution,
    or dynamic DOM manipulation prevents Tier 1 HTTP extraction.

    Features:
    - Retry loop with exponential backoff + jitter (matches HttpScraper pattern)
    - Per-domain token bucket rate limiting via DomainRateLimiter
    - RFC 9309 robots.txt compliance with TTL-cached parser
    - Heavy resource blocking (images/fonts) for faster DOM rendering
    - Optional CSS selector waiting for dynamic content
    - Full/viewport screenshot capture support
    - Proxy support via BaseScraper.get_proxy()
    """
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 2,
        user_agent: Optional[str] = None,
        headless: bool = True,
        block_heavy_resources: bool = True,
        robots_parser: Optional[Any] = None,
        rate_limiter: Optional[DomainRateLimiter] = None,
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
        self.headless = headless
        self.block_heavy_resources = block_heavy_resources
        self.rate_limiter = rate_limiter or DomainRateLimiter()

        if robots_parser is None:
            from .robots_parser import RobotsParser
            self.robots = RobotsParser()
        else:
            self.robots = robots_parser

    async def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        capture_screenshot: bool = False,
        **kwargs: Any
    ) -> ScrapedResult:
        start_time = time.perf_counter()

        # 1. robots.txt compliance check
        try:
            if not await self.robots.can_fetch(url, self.user_agent or self.DEFAULT_USER_AGENT):
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ScrapedResult(
                    url=url,
                    status_code=403,
                    html="",
                    error="Disallowed by robots.txt",
                    elapsed_ms=elapsed_ms,
                    metadata={"tier": "browser_tier3"}
                )
        except Exception:
            pass  # Fail open on robots check error

        # 2. Rate limiting backpressure
        try:
            crawl_delay = await self.robots.get_crawl_delay(
                url, self.user_agent or self.DEFAULT_USER_AGENT
            )
        except Exception:
            crawl_delay = None
        await self.rate_limiter.acquire(url, custom_delay=crawl_delay)

        # 3. Verify Playwright availability
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ScrapedResult(
                url=url,
                status_code=500,
                html="",
                error="Playwright is not installed or available in this environment",
                elapsed_ms=elapsed_ms,
                metadata={"tier": "browser_tier3"}
            )

        # 4. Retry loop with exponential backoff + jitter
        attempt = 0
        backoff_base = 2.0
        last_error: Optional[str] = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                result = await self._execute_browser_scrape(
                    url=url,
                    async_playwright=async_playwright,
                    wait_for_selector=wait_for_selector,
                    capture_screenshot=capture_screenshot,
                    start_time=start_time,
                    attempt=attempt,
                )
                # Success or non-retryable status
                if result.status_code < 500 or attempt >= self.max_retries:
                    return result

                # Server error — retry with backoff
                last_error = result.error
                wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                logger.warning(
                    "Browser scrape HTTP %d for %s (attempt %d/%d). Backing off %.2fs",
                    result.status_code, url, attempt, self.max_retries, wait
                )
                await asyncio.sleep(wait)

            except Exception as err:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                last_error = f"BrowserScrapeError: {err}"
                logger.error(
                    "Browser scraping failed for %s (attempt %d/%d): %s",
                    url, attempt, self.max_retries, err
                )
                if attempt >= self.max_retries:
                    return ScrapedResult(
                        url=url,
                        status_code=500,
                        html="",
                        error=last_error,
                        elapsed_ms=elapsed_ms,
                        metadata={"tier": "browser_tier3", "attempts": attempt}
                    )
                wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                await asyncio.sleep(wait)

        # Exhausted retries
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return ScrapedResult(
            url=url,
            status_code=500,
            html="",
            error=last_error or "Exceeded maximum retry attempts",
            elapsed_ms=elapsed_ms,
            metadata={"tier": "browser_tier3", "attempts": attempt}
        )

    async def _execute_browser_scrape(
        self,
        url: str,
        async_playwright: Any,
        wait_for_selector: Optional[str],
        capture_screenshot: bool,
        start_time: float,
        attempt: int,
    ) -> ScrapedResult:
        """Execute a single browser scrape attempt."""
        # Resolve proxy for this attempt
        proxy_url = self.get_proxy()
        proxy_config = {"server": proxy_url} if proxy_url else None

        # Resolve user agent (rotate on each attempt)
        ua = self.user_agent or self.rotate_user_agent()

        async with async_playwright() as p:
            launch_args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            browser = await p.chromium.launch(
                headless=self.headless,
                args=launch_args,
                proxy=proxy_config,
            )
            context = await browser.new_context(
                user_agent=ua,
                viewport={"width": 1280, "height": 800},
                locale="en-US"
            )
            page = await context.new_page()

            # Block heavy media resources to accelerate rendering
            if self.block_heavy_resources:
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf}",
                    lambda route: route.abort()
                )

            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=int(self.timeout * 1000)
            )

            if wait_for_selector:
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=5000)
                except Exception:
                    logger.warning(
                        "Timeout waiting for selector %s on %s", wait_for_selector, url
                    )

            status_code = response.status if response else 200
            html = await page.content()
            headers = response.headers if response else {}

            screenshot_bytes = None
            if capture_screenshot:
                screenshot_bytes = await page.screenshot(full_page=False)

            await browser.close()
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            metadata: Dict[str, Any] = {
                "tier": "browser_tier3",
                "rendered_js": True,
                "has_screenshot": screenshot_bytes is not None,
                "attempts": attempt,
            }
            if proxy_url:
                metadata["proxy_used"] = True

            return ScrapedResult(
                url=url,
                status_code=status_code,
                html=html,
                headers=headers,
                is_modified=True,
                elapsed_ms=elapsed_ms,
                metadata=metadata
            )
