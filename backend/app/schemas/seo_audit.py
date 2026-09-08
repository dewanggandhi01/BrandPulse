from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List, Dict
from uuid import UUID
from datetime import datetime

class SeoIssue(BaseModel):
    id: str
    pillar: str
    severity: str
    title: str
    description: str
    recommendation: str

class SeoAuditRead(BaseModel):
    id: UUID
    snapshot_id: UUID
    total_score: int
    technical_scores: Optional[Dict[str, Any]] = None
    content_scores: Optional[Dict[str, Any]] = None
    structured_data_scores: Optional[Dict[str, Any]] = None
    link_scores: Optional[Dict[str, Any]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    audited_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SeoAuditHistoryItem(BaseModel):
    id: UUID
    total_score: int
    technical_score: int
    content_score: int
    structured_data_score: int
    link_score: int
    audited_at: datetime

class SeoAuditHistoryResponse(BaseModel):
    items: List[SeoAuditHistoryItem]
    brand_id: UUID
    latest_score: Optional[int] = None
