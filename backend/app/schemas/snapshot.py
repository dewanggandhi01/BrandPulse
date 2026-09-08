from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List, Dict
from uuid import UUID
from datetime import datetime

class SnapshotRead(BaseModel):
    id: UUID
    brand_url_id: UUID
    scrape_job_id: Optional[UUID] = None
    content_hash: str
    html_size: int
    status_code: int
    headers: Optional[Dict[str, Any]] = None
    captured_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SnapshotDetailRead(SnapshotRead):
    html_content: Optional[str] = None

class SnapshotListResponse(BaseModel):
    items: List[SnapshotRead]
    total: int
    page: int
    size: int
    pages: int
