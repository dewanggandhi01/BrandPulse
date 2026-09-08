from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text, String, Boolean, ForeignKey
from datetime import datetime
from app.database import Base
import uuid

class Brand(Base):
    __tablename__ = 'brand'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255))
    metadata_info: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(server_default=text('now()'), onupdate=text('now()'))
    
    urls: Mapped[list["BrandUrl"]] = relationship("BrandUrl", back_populates="brand", cascade="all, delete-orphan")


class BrandUrl(Base):
    __tablename__ = 'brand_url'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('brand.id', ondelete='CASCADE'))
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_type: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(server_default=text('now()'), onupdate=text('now()'))
    
    brand: Mapped["Brand"] = relationship("Brand", back_populates="urls")
