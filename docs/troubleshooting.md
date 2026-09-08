# BrandPulse Troubleshooting Guide

This guide provides a structured **Symptom → Root Cause → Resolution Matrix** for diagnosing and fixing common issues across the BrandPulse application stack.

---

## 1. Symptom → Cause → Resolution Matrix

| Symptom | Root Cause | Immediate Resolution | Permanent Fix |
|---|---|---|---|
| **Crawl Job Fails with HTTP 429 (Too Many Requests)** | Target domain rate limiter triggered or token bucket depleted. | Back off crawl interval and retry manually. | Configure domain-specific token bucket rate in `DomainRateLimiter` to reduce requests/second. |
| **Crawl Job Fails with HTTP 403 / Cloudflare Challenge** | Target site requires JavaScript execution or bot challenge solved. | Escalate scrape job tier from `tier1_http` to `tier3_playwright`. | Ensure Playwright user-agent rotation and viewport emulation are enabled. |
| **Playwright Chromium Process Hangs / Worker Out of Memory** | Browser context not properly closed after unhandled scraping timeout. | Run `pkill -f chrome` on worker container; restart `celery-scraping`. | Enforce `--pool=solo` on scraping worker and wrap browser lifecycle in `async with async_playwright()`. |
| **FastAPI Returns 500 "QueuePool limit exceeded"** | Async SQLAlchemy sessions leaking without commit/rollback or pool size too small. | Restart backend service to clear stale connections. | Verify all endpoints use `Depends(get_db)` context generator; adjust `pool_size` and `max_overflow`. |
| **Celery Tasks Remain in `PENDING` Indefinitely** | Redis broker offline or Celery worker not listening on target queue. | Check `redis-cli ping`; inspect worker queues with `celery -A workers.celery_app inspect active_queues`. | Ensure docker-compose specifies explicit queue flags: `-Q scraping` and `-Q analysis,seo,diffing`. |
| **Frontend Displays "CORS Request Blocked"** | Origin header does not match backend `CORS_ORIGINS` settings. | Add client origin (e.g. `http://localhost:5173`) to `.env` `CORS_ORIGINS`. | Restart backend to reload CORS middleware configuration. |
| **Diffing Engine Times Out on Massive HTML DOM** | Uncleaned minified single-line scripts/SVG trees causing exponential diff complexity. | Pre-clean snapshot using `HtmlCleaner.clean_html()` before running comparator. | `workers/diffing/cleaner.py` strips script, style, SVG, and comments before diff computation. |

---

## 2. Deep-Dive Diagnostics

### A. Diagnosing Scraping Worker Issues
```bash
# Check Celery scraping worker logs
docker logs brandpulse-celery-scraping -f --tail 100

# Inspect active scraping tasks in Redis
docker exec -it brandpulse-redis redis-cli -n 1 LLEN scraping
```

### B. Diagnosing Database Locks & Active Queries
```sql
-- Query long-running database queries
SELECT pid, now() - query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Terminate a stuck transaction if necessary
SELECT pg_terminate_backend(<pid>);
```

### C. Testing Redis Connectivity
```bash
# Ping Redis broker
docker exec -it brandpulse-redis redis-cli ping
# Expected response: PONG
```

---

## 3. Escalation & Bug Reporting

If an issue cannot be resolved using this guide:
1. Capture the correlation ID from the response header: `X-Request-ID`.
2. Collect the structured JSON logs from the backend matching that ID.
3. Open an issue with the full stack trace and reproduction steps.
