from sqlalchemy import Column, Integer, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Review(BaseModel):
    __tablename__ = "reviews"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 звезд
    comment = Column(Text, nullable=True)
    images = Column(JSON, nullable=True)  # Массив путей к фото отзыва

    # Связи
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review(user_id='{self.user_id}', rating={self.rating})>"


class ViewHistory(BaseModel):
    __tablename__ = "view_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Связи
    user = relationship("User", back_populates="view_history")
    product = relationship("Product", back_populates="view_history")

    def __repr__(self):
        return f"<ViewHistory(user_id='{self.user_id}', product_id='{self.product_id}')>"


class Favorite(BaseModel):
    __tablename__ = "favorites"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Связи
    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite(user_id='{self.user_id}', product_id='{self.product_id}')>"