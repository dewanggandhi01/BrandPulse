from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, String, ForeignKey, Integer, Text
from datetime import datetime
from app.database import Base
import uuid
from .brand import BrandUrl
from .scrape_job import ScrapeJob

class Snapshot(Base):
    __tablename__ = 'snapshot'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_url_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand_url.id', ondelete='CASCADE'))
    scrape_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('scrape_job.id', ondelete='SET NULL'), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    html_size: Mapped[int] = mapped_column(Integer)
    status_code: Mapped[int] = mapped_column(Integer)
    headers: Mapped[dict | None] = mapped_column(JSON)
    html_path: Mapped[str] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    brand_url: Mapped["BrandUrl"] = relationship("BrandUrl")
    scrape_job: Mapped["ScrapeJob"] = relationship("ScrapeJob")
