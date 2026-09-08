from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

class BrandBase(BaseModel):
    name: str
    domain: str
    industry: Optional[str] = None
    metadata_info: Optional[Any] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BrandBase):
    name: Optional[str] = None
    domain: Optional[str] = None

class BrandRead(BrandBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BrandListResponse(BaseModel):
    items: List[BrandRead]
    total: int
    page: int
    size: int
    pages: int
