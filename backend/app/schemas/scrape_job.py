from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, List
from uuid import UUID
from datetime import datetime

class ScrapeJobBase(BaseModel):
    brand_id: UUID
    job_type: str = "website_crawl"
    status: str = "pending"
    config: Optional[Any] = None

class ScrapeJobCreate(BaseModel):
    brand_id: UUID
    job_type: str = "website_crawl"
    seed_urls: Optional[List[str]] = None
    max_depth: int = Field(default=1, ge=0, le=3)
    max_pages: int = Field(default=10, ge=1, le=50)
    tier: str = Field(default="auto", description="Scraping tier: auto, http, browser")

class ScrapeJobRead(ScrapeJobBase):
    id: UUID
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ScrapeJobListResponse(BaseModel):
    items: List[ScrapeJobRead]
    total: int
    page: int
    size: int
    pages: int
