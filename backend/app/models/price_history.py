from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, String, ForeignKey, Numeric, Index
from datetime import datetime
from app.database import Base
import uuid
from .product import Product
from decimal import Decimal

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    __table_args__ = (
        Index('ix_price_history_captured_at_brin', 'captured_at', postgresql_using='brin'),
        Index('ix_price_history_product_captured_at', 'product_id', text('captured_at DESC')),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('product.id', ondelete='CASCADE'))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10))
    captured_at: Mapped[datetime] = mapped_column(server_default=text('now()'))
    
    product: Mapped["Product"] = relationship("Product")
