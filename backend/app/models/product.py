from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, String, ForeignKey, Numeric
from datetime import datetime
from app.database import Base
import uuid
from .snapshot import Snapshot
from .brand import Brand
from decimal import Decimal

class Product(Base):
    __tablename__ = 'product'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('snapshot.id', ondelete='SET NULL'), nullable=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str | None] = mapped_column(String(100))
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    availability: Mapped[str | None] = mapped_column(String(50))
    image_url: Mapped[str | None] = mapped_column(String(2048))
    attributes: Mapped[dict | None] = mapped_column(JSON)
    data_source_tag: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(server_default=text('now()'), onupdate=text('now()'))
    
    snapshot: Mapped["Snapshot"] = relationship("Snapshot")
    brand: Mapped["Brand"] = relationship("Brand")
