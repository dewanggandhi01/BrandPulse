from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

class PriceHistoryRead(BaseModel):
    id: UUID
    product_id: UUID
    price: Decimal
    currency: str
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductRead(BaseModel):
    id: UUID
    snapshot_id: Optional[UUID] = None
    brand_id: UUID
    name: str
    sku: Optional[str] = None
    current_price: Optional[Decimal] = None
    currency: Optional[str] = "USD"
    availability: Optional[str] = "InStock"
    image_url: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    data_source_tag: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProductDetailRead(ProductRead):
    price_history: List[PriceHistoryRead] = []

class ProductListResponse(BaseModel):
    items: List[ProductRead]
    total: int
    page: int
    size: int
    pages: int

class ProductAnalyticsSummary(BaseModel):
    total_products: int
    in_stock_count: int
    out_of_stock_count: int
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: str = "USD"
    price_changes_count: int = 0
