from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, String, ForeignKey, Text
from datetime import datetime
from app.database import Base
import uuid
from .brand import Brand

class Mention(Base):
    __tablename__ = 'mention'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    source: Mapped[str] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    brand: Mapped["Brand"] = relationship("Brand")
    sentiment: Mapped["Sentiment | None"] = relationship("Sentiment", back_populates="mention", uselist=False, cascade="all, delete-orphan")
