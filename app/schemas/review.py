from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

''' Модель отзыва '''
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description='Рейтинг от 1 до 5 звезд')
    comment: Optional[str] = Field(None, max_length=2000, description='Текст отзыва')


''' Модель создания отзыва '''
class ReviewCreate(ReviewBase):
    product_id: uuid.UUID = Field(..., description='Идентификатор отзыва')


''' Модель обновления отзыва '''
class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description='Рейтинг от 1 до 5 звезд')
    comment: Optional[str] = Field(None, max_length=2000, description='Текст отзыва')
    is_approved: Optional[bool] = Field(None, description='Настройка модерации отзыва (Одобрен)')
    is_hidden: Optional[bool] = Field(None, description='Настройка модерации отзыва (Не одобрен)')


''' Модель загрузки изображений к отзыву '''
class ReviewImageUpload(BaseModel):
    review_id: uuid.UUID = Field(..., description='Идентификатор отзыва, к которому добавляется изображение')


''' Краткая информация о пользователе в отзыве '''
class UserInReview(BaseModel):
    id: uuid.UUID = Field(..., description='Идентификатор пользователя')
    username: str = Field(..., description='UserName пользователя')
    full_name: Optional[str] = Field(None, description='Полное имя пользователя (Опционально)')

    ''' Берем информацию насчет пользователя '''
    class Config:
        from_attributes = True


''' Модель содержит краткую информацию о продукте '''
class ProductInReview(BaseModel):
    id: uuid.UUID = Field(..., description='уникальный идентификатор отзыва')
    name: str = Field(..., description='Название товара')
    main_image: Optional[str] = Field(None, description='Необязательная ссылка на главное изображение товара')

    class Config:
        from_attributes = True


''' Полный отзыв '''
class Review(ReviewBase):
    id: uuid.UUID = Field(..., description='Уникальный идентификатор отзыва')
    user_id: uuid.UUID = Field(..., description='Привязка с пользователем')
    product_id: uuid.UUID = Field(..., description='Привязка с продуктом')
    images: List[str] = Field(None, description='Список URL изображений, связанных с отзывом')
    is_approved: bool = Field(True, description='Настройка модерации отзыва (Одобрен)')
    is_hidden: bool = Field(False, description='Настройка модерации отзыва (Не одобрен)')
    created_at: datetime = Field(..., description='Время создания комментария')
    updated_at: datetime = Field(..., description='Время обновления комментария')

    ''' UserInReview, ProductInReview '''
    user: Optional[UserInReview] = Field(None, description='Информация о пользователе')
    product: Optional[ProductInReview] = Field(None, description='Информация о продукте')

    ''' Дополнительные поля '''
    helpful_count: Optional[int] = Field(0, description='Лайк')
    not_helpful_count: Optional[int] = Field(0, description='Дизлайк')
    user_helpful_vote: Optional[bool] = Field(None, description='Оценка текущего пользователя')

    class Config:
        from_attributes = True


''' Список пользователей с пагинацией '''
class ReviewList(BaseModel):
    reviews: List[Review] = Field(..., description='Список объектов')
    total: int = Field(..., description='Общее количество отзывов')
    page: int = Field(..., description='Текущая страница')
    size: int = Field(..., description='Отзывов на странице')
    pages: int = Field(..., description='Общее количество страниц')


''' Статистика отзывов '''
class ReviewStats(BaseModel):
    total_reviews: int = Field(..., description='Общее количество отзывов')
    average_rating: float = Field(..., description='Средний рейтинг отзывов')
    rating_distribution: dict = Field(..., description='Словарь с распределением отзывов')


''' Схема голосов за полезность '''
class ReviewHelpfulCreate(BaseModel):
    is_helpful: bool = Field(..., description='Используется для запроса добавления голоса за полезность')


''' Схема голосов за полезность '''
class ReviewHelpful(BaseModel):
    id: uuid.UUID = Field(..., description='ID')
    review_id: uuid.UUID = Field(..., description='ID комментария')
    user_id: uuid.UUID = Field(..., description='ID пользователя')
    is_helpful: bool = Field(..., description='Лайки')
    created_at: datetime = Field(..., description='Время создания')

    class Config:
        from_attributes = True