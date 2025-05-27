from sqlalchemy import Column, Integer, Text, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models import BaseModel


''' Таблица отзывов пользователей на товары '''
class Review(BaseModel):
    __tablename__ = "reviews"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False) # ID пользователя
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False) # ID продукта
    rating = Column(Integer, nullable=False)  # Рейтинг товара (1-5)
    comment = Column(Text, nullable=True) # Комментарии к товару
    images = Column(JSON, nullable=True)  # JSON-структура с массива путей к изображениям

    ''' Создаем связь между таблицами User, Product '''
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")


    ''' Пример отображения объекта '''
    def __repr__(self):
        return f"<Review(user_id='{self.user_id}', rating={self.rating})>"

''' Таблица оценки отзывов '''
class ReviewHelpful(BaseModel):
    __tablename__ = "review_helpfuls"

    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False) # ID отзыва
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False) # ID пользователя
    helpful = Column(Boolean, nullable=False)  # True, если отзыв был полезным, иначе False

    ''' Создаем связь между таблицами Review, User '''
    review = relationship("Review", back_populates="helpful_votes")
    user = relationship("User", back_populates="helpful_reviews")


    ''' Пример отображения объекта '''
    def __repr__(self):
        return f"<ReviewHelpful(review_id='{self.review_id}', user_id='{self.user_id}', helpful={self.helpful})>"