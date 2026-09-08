from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Any, Dict, List, Optional

class CompetitorLinkCreate(BaseModel):
    competitor_brand_id: UUID

class CompetitorRead(BaseModel):
    id: UUID
    brand_id: UUID
    competitor_brand_id: UUID
    competitor_name: str
    competitor_domain: str
    industry: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BrandBenchmarkProfile(BaseModel):
    brand_id: UUID
    brand_name: str
    domain: str
    seo_total_score: Optional[int] = None
    technical_score: Optional[int] = None
    content_score: Optional[int] = None
    structured_data_score: Optional[int] = None
    link_score: Optional[int] = None
    product_count: int = 0
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: Optional[str] = "USD"
    in_stock_rate: Optional[float] = None

class CompetitorComparisonMatrix(BaseModel):
    target_brand: BrandBenchmarkProfile
    competitors: List[BrandBenchmarkProfile]
    price_index: Optional[float] = None
    radar_data: List[Dict[str, Any]]

class CompetitorSyncResponse(BaseModel):
    message: str
    synced_brands: int
    jobs_dispatched: int
    job_ids: List[UUID] = []

