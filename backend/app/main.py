from __future__ import annotations
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import health, brands, scrape_jobs, snapshots, seo, products, changes, competitors, mentions, ads, reports
from app.middleware.cors import setup_cors
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.rate_limit import SimpleRateLimitMiddleware
from app.middleware.error_handler import setup_error_handlers
from app.utils.logging import setup_logging
from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Create tables on startup for dev (skip if already exist)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        import structlog
        structlog.get_logger().warning("Skipping table creation (tables or types already exist)", error=str(exc))
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="BrandPulse API", lifespan=lifespan)
    
    setup_cors(app)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SimpleRateLimitMiddleware, max_requests=100, window=60)
    setup_error_handlers(app)
    
    prefixes = [settings.API_V1_PREFIX]
    if settings.API_V1_PREFIX != "/api":
        prefixes.append("/api")

    for p in prefixes:
        app.include_router(health.router, prefix=p, tags=["health"])
        app.include_router(brands.router, prefix=f"{p}/brands", tags=["brands"])
        app.include_router(scrape_jobs.router, prefix=f"{p}/scrape-jobs", tags=["scrape-jobs"])
        app.include_router(snapshots.router, prefix=f"{p}/snapshots", tags=["snapshots"])
        app.include_router(seo.router, prefix=f"{p}/seo", tags=["seo"])
        app.include_router(products.router, prefix=f"{p}/products", tags=["products"])
        app.include_router(changes.router, prefix=f"{p}/changes", tags=["changes"])
        app.include_router(competitors.router, prefix=f"{p}/competitors", tags=["competitors"])
        app.include_router(mentions.router, prefix=f"{p}/mentions", tags=["mentions"])
        app.include_router(ads.router, prefix=f"{p}/ads", tags=["ads"])
        app.include_router(reports.router, prefix=f"{p}/reports", tags=["reports"])
    
    return app

app = create_app()
