from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class ViewHistory(Base):
    __tablename__ = "view_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="view_history")
    product = relationship("Product", back_populates="view_history")

    # Indexes for performance
    __table_args__ = (
        Index('ix_view_history_user_id', 'user_id'),
        Index('ix_view_history_product_id', 'product_id'),
        Index('ix_view_history_viewed_at', 'viewed_at'),
        Index('ix_view_history_user_viewed', 'user_id', 'viewed_at'),  # для сортировки по дате
    )


class Favorites(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")

    # Unique constraint - один товар может быть в избранном у пользователя только один раз
    __table_args__ = (
        Index('ix_favorites_user_id', 'user_id'),
        Index('ix_favorites_product_id', 'product_id'),
        Index('uq_user_product_favorite', 'user_id', 'product_id', unique=True),
    )