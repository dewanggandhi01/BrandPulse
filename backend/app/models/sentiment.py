from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, String, ForeignKey, Float
from datetime import datetime
from app.database import Base
import uuid
from .mention import Mention

class Sentiment(Base):
    __tablename__ = 'sentiment'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    mention_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('mention.id', ondelete='CASCADE'))
    label: Mapped[str] = mapped_column(String(50))
    positive_score: Mapped[float] = mapped_column(Float)
    negative_score: Mapped[float] = mapped_column(Float)
    neutral_score: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    mention: Mapped["Mention"] = relationship("Mention", back_populates="sentiment")
