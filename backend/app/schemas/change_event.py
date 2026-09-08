from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Any, Dict, List, Optional

class ChangeEventRead(BaseModel):
    id: UUID
    snapshot_id: UUID
    previous_snapshot_id: Optional[UUID] = None
    change_type: str
    similarity_ratio: Optional[float] = None
    ai_summary: Optional[str] = None
    created_at: datetime
    additions_count: Optional[int] = None
    deletions_count: Optional[int] = None
    total_changes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ChangeEventDetailRead(ChangeEventRead):
    diff_details: Optional[Dict[str, Any]] = None

class ChangeEventListResponse(BaseModel):
    items: List[ChangeEventRead]
    total: int
    page: int
    size: int
    pages: int

class ChangeComparisonRequest(BaseModel):
    snapshot_id: UUID
    previous_snapshot_id: Optional[UUID] = None

class ChangeAnalyticsSummary(BaseModel):
    total_changes: int
    pricing_changes_count: int
    messaging_pivots_count: int
    layout_overhauls_count: int
    seo_changes_count: int
    minor_copy_count: int
    avg_similarity: Optional[float] = None

class ChangeScanResponse(BaseModel):
    message: str
    urls_scanned: int
    snapshots_evaluated: int
    changes_detected: int
    total_events: int

