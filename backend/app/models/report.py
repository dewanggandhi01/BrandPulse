from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, String, ForeignKey, Text
from datetime import datetime
from app.database import Base
import uuid
from .brand import Brand

class Report(Base):
    __tablename__ = 'report'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    report_type: Mapped[str] = mapped_column(String(100))
    content: Mapped[dict | None] = mapped_column(JSON)
    ai_narrative: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    brand: Mapped["Brand"] = relationship("Brand")
