from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from uuid import UUID
from typing import Any

class AdIntelBase(BaseModel):
    platform: str = Field(..., description="Advertising network: google, meta, linkedin, twitter, tiktok")
    ad_text: str | None = Field(default=None, description="Creative copy / body text")
    ad_format: str | None = Field(default=None, description="search, display, video, sponsored_feed")
    target_url: str | None = Field(default=None, description="Destination landing page URL")
    first_seen: date | None = None
    last_seen: date | None = None
    targeting_info: dict[str, Any] | None = None
    data_source_tag: str | None = "ad_transparency"

class AdIntelCreate(AdIntelBase):
    pass

class AdIntelBatchCreate(BaseModel):
    ads: list[AdIntelCreate] = Field(..., min_length=1)

class AdIntelRead(AdIntelBase):
    id: UUID
    brand_id: UUID
    created_at: datetime | None = None
    longevity_days: int | None = None
    spend_tier: str | None = None
    is_evergreen: bool | None = None
    headline: str | None = None
    cta: str | None = None

    model_config = ConfigDict(from_attributes=True)

class AdIntelListResponse(BaseModel):
    items: list[AdIntelRead]
    total: int
    page: int
    size: int
    pages: int

class PlatformShare(BaseModel):
    platform: str
    count: int
    percentage: float

class FormatShare(BaseModel):
    format: str
    count: int
    percentage: float

class SpendTierShare(BaseModel):
    tier: str
    count: int
    percentage: float

class TopItem(BaseModel):
    name: str
    count: int

class AdIntelAnalyticsResponse(BaseModel):
    brand_id: UUID
    total_ads: int
    evergreen_count: int
    platform_distribution: list[PlatformShare]
    format_distribution: list[FormatShare]
    spend_tier_distribution: list[SpendTierShare]
    top_ctas: list[TopItem]
    top_landing_domains: list[TopItem]
    estimated_monthly_spend_range: str

class AdParsePreviewRequest(BaseModel):
    raw_text: str = Field(..., min_length=1)
    target_url: str | None = None
    suggested_format: str | None = None

class AdParsePreviewResponse(BaseModel):
    headline: str | None
    body_copy: str
    cta: str | None
    detected_format: str
    landing_page_domain: str | None
    utm_parameters: dict[str, str]
    longevity_days: int
    spend_tier: str
    is_evergreen: bool
