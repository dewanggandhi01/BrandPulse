from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, ForeignKey, Index
from datetime import datetime
from app.database import Base
import uuid
from .brand import Brand

class Competitor(Base):
    __tablename__ = 'competitor'
    
    __table_args__ = (
        Index('ix_competitor_brand_competitor', 'brand_id', 'competitor_brand_id', unique=True),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    competitor_brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(server_default=text('now()'), onupdate=text('now()'))
    
    brand: Mapped["Brand"] = relationship("Brand", foreign_keys=[brand_id])
    competitor_brand: Mapped["Brand"] = relationship("Brand", foreign_keys=[competitor_brand_id])
