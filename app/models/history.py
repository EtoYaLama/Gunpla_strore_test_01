from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


''' История просмотренных товаров пользователя '''
class ViewHistory(Base):
    __tablename__ = "view_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Генерируем уникальное ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    ''' Создаем связь между таблицами User и Product '''
    user = relationship("User", back_populates="view_history")
    product = relationship("Product", back_populates="view_history")

    ''' Индексы для повышения производительности запросов '''
    __table_args__ = (
        Index('ix_view_history_user_id', 'user_id'), # используются в фильтрах
        Index('ix_view_history_product_id', 'product_id'), # используются в фильтрах
        Index('ix_view_history_viewed_at', 'viewed_at'), # используется для сортировки по времени
        Index('ix_view_history_user_viewed', 'user_id', 'viewed_at'),  # для ускорения сортировки по времени просмотров конкретного пользователя
    )


'''  Избранные товары пользователя '''
class Favorites(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Генерируем уникальное ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    ''' Создаем связь между таблицами User и Product '''
    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")

    ''' Индексы для повышения производительности запросов '''
    __table_args__ = (
        Index('ix_favorites_user_id', 'user_id'), # используются в фильтрах
        Index('ix_favorites_product_id', 'product_id'), # используются в фильтрах
        Index('uq_user_product_favorite', 'user_id', 'product_id', unique=True), # Установка, что каждый пользователь может добавить в избранное один и тот же товар только один раз

    )