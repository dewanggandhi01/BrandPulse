from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, String, ForeignKey, Text, Date
from datetime import datetime, date
from app.database import Base
import uuid
from .brand import Brand

class AdIntel(Base):
    __tablename__ = 'ad_intel'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    platform: Mapped[str] = mapped_column(String(100))
    ad_text: Mapped[str | None] = mapped_column(Text)
    ad_format: Mapped[str | None] = mapped_column(String(100))
    target_url: Mapped[str | None] = mapped_column(String(2048))
    first_seen: Mapped[date | None] = mapped_column(Date)
    last_seen: Mapped[date | None] = mapped_column(Date)
    targeting_info: Mapped[dict | None] = mapped_column(JSON)
    data_source_tag: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    brand: Mapped["Brand"] = relationship("Brand")
