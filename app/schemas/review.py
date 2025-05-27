from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import uuid


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5 звезд")
    comment: Optional[str] = Field(None, max_length=2000, description="Текст отзыва")


class ReviewCreate(ReviewBase):
    product_id: uuid.UUID


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)
    is_approved: Optional[bool] = None
    is_hidden: Optional[bool] = None


class ReviewImageUpload(BaseModel):
    """Схема для загрузки изображений к отзыву"""
    review_id: uuid.UUID


class UserInReview(BaseModel):
    """Пользователь в отзыве (краткая информация)"""
    id: uuid.UUID
    username: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductInReview(BaseModel):
    """Товар в отзыве (краткая информация)"""
    id: uuid.UUID
    name: str
    main_image: Optional[str] = None

    class Config:
        from_attributes = True


class Review(ReviewBase):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    images: List[str] = []
    is_approved: bool = True
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime

    # Relationships
    user: Optional[UserInReview] = None
    product: Optional[ProductInReview] = None

    # Calculated fields
    helpful_count: Optional[int] = 0
    not_helpful_count: Optional[int] = 0
    user_helpful_vote: Optional[bool] = None  # для текущего пользователя

    class Config:
        from_attributes = True


class ReviewList(BaseModel):
    """Список отзывов с пагинацией"""
    reviews: List[Review]
    total: int
    page: int
    size: int
    pages: int


class ReviewStats(BaseModel):
    """Статистика отзывов для товара"""
    total_reviews: int
    average_rating: float
    rating_distribution: dict  # {1: 5, 2: 10, 3: 15, 4: 20, 5: 25}


class ReviewHelpfulCreate(BaseModel):
    is_helpful: bool


class ReviewHelpful(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    user_id: uuid.UUID
    is_helpful: bool
    created_at: datetime

    class Config:
        from_attributes = True