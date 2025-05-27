from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, List
from app.schemas import ProductBase


''' Модель истории просмотров '''
class ViewHistoryBase(BaseModel):
    user_id: UUID4 = Field(..., description='ID Пользователя')
    product_id: UUID4 = Field(..., description='ID Продукта')


''' Модель для создания записей (Истории просмотренных товаров) '''
class ViewHistoryCreate(ViewHistoryBase):
    pass


''' Модель описания возвращаемых данных о просмотренной записи '''
class ViewHistoryResponse(ViewHistoryBase):
    id: UUID4 = Field(..., description='ID Просмотра')
    viewed_at: datetime = Field(..., description='Дата и время просмотра')
    product: Optional[ProductBase] = Field(None, description='Вложенный объект')

    ''' Берем информацию насчет продукта '''
    class Config:
        from_attributes = True


''' Модель ответа для запросов просмотренных товаров '''
class ViewHistoryList(BaseModel):
    items: List[ViewHistoryResponse] = Field(..., description='Список объектов')
    total: int = Field(..., description='Общее количество записей')
    page: int = Field(..., description='Текущая страница')
    size: int = Field(..., description='Сколько записей на одной странице')
    pages: int = Field(..., description='Общее количество страниц')


''' Модель избранные '''
class FavoritesBase(BaseModel):
    user_id: UUID4 = Field(..., description='ID Пользователя')
    product_id: UUID4 = Field(..., description='ID Продукта')


''' Модель для добавления продукта в избранные '''
class FavoritesCreate(BaseModel):
    product_id: UUID4 = Field(..., description='ID Продукта')


''' Модель ответа для Избранного '''
class FavoritesResponse(FavoritesBase):
    id: UUID4 = Field(..., description='ID Просмотра')
    created_at: datetime = Field(..., description='Время добавления в избранное')
    product: Optional[ProductBase] = Field(None, description='Подробности о самом продукте')

    ''' Берем информацию насчет продукта '''
    class Config:
        from_attributes = True


''' Модель для ответа запроса списка избранных товаров '''
class FavoritesList(BaseModel):
    items: List[FavoritesResponse] = Field(..., description='Массив избранных товаров')
    total: int = Field(..., description='Общее количество записей')
    page: int = Field(..., description='Текущая страница')
    size: int = Field(..., description='Сколько записей на одной странице')
    pages: int = Field(..., description='Общее количество страниц')


''' Модель ответа при добавлении/удалении товаров из избранных '''
class FavoritesToggleResponse(BaseModel):
    is_favorite: bool = Field(..., description='Включен ли товар в избранные')
    message: str = Field(..., description='Сообщение о выполненном действии')


''' Модель индикатор, добавлен ли товар в избранное '''
class ProductWithFavoriteStatus(ProductBase):
    is_favorite: bool = Field(False, description='Индикатор, добавлен ли товар в избранное')

    ''' Берем информацию насчет продукта '''
    class Config:
        from_attributes = True
