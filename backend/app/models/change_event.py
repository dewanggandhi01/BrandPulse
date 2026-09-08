from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, String, ForeignKey, Float, Text
from datetime import datetime
from app.database import Base
import uuid
from .snapshot import Snapshot

class ChangeEvent(Base):
    __tablename__ = 'change_event'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('snapshot.id', ondelete='CASCADE'))
    previous_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('snapshot.id', ondelete='SET NULL'), nullable=True)
    change_type: Mapped[str] = mapped_column(String(50))
    similarity_ratio: Mapped[float | None] = mapped_column(Float)
    diff_details: Mapped[dict | None] = mapped_column(JSON)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", foreign_keys=[snapshot_id])
    previous_snapshot: Mapped["Snapshot"] = relationship("Snapshot", foreign_keys=[previous_snapshot_id])
