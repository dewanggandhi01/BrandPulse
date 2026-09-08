from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, ForeignKey, Float
from datetime import datetime
from app.database import Base
import uuid
from .snapshot import Snapshot

class SeoAudit(Base):
    __tablename__ = 'seo_audit'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('snapshot.id', ondelete='CASCADE'))
    total_score: Mapped[float] = mapped_column(Float)
    technical_scores: Mapped[dict | None] = mapped_column(JSON)
    content_scores: Mapped[dict | None] = mapped_column(JSON)
    structured_data_scores: Mapped[dict | None] = mapped_column(JSON)
    link_scores: Mapped[dict | None] = mapped_column(JSON)
    issues: Mapped[dict | None] = mapped_column(JSON)
    audited_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    snapshot: Mapped["Snapshot"] = relationship("Snapshot")
