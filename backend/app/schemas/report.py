from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from typing import Any

class ReportCreate(BaseModel):
    report_type: str = Field(default="executive_brief", description="executive_brief, competitor_benchmark, seo_audit")

class SwotItem(BaseModel):
    category: str = Field(..., description="strength, weakness, opportunity, threat")
    title: str
    description: str
    impact: str = Field(default="medium", description="high, medium, low")

class ReportRead(BaseModel):
    id: UUID
    brand_id: UUID
    report_type: str
    content: dict[str, Any] | None = None
    ai_narrative: str | None = None
    generated_at: datetime
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class ReportListResponse(BaseModel):
    items: list[ReportRead]
    total: int
    page: int
    size: int
    pages: int

class GenerateReportResponse(BaseModel):
    message: str
    report: ReportRead
