from pydantic import BaseModel, validator, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid
from app.models import GradeEnum


''' Модель для описании продукта '''
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description='Название товара')
    description: Optional[str] = Field(None, max_length=2000, description='Описание товара')
    price: Decimal = Field(..., gt=0, description='Цена товара')
    grade: GradeEnum = Field(..., description='Grade модели')
    manufacturer: str = Field(..., min_length=1, max_length=100, description='Производитель')
    series: Optional[str] = Field(None, max_length=100, description='Серия')
    scale: Optional[str] = Field(None, max_length=20, description='Масштаб')
    difficulty: Optional[int] = Field(None, ge=1, le=5, description='Сложность (1-5)')
    in_stock: int = Field(default=0, ge=0, description='Количество в наличии')


''' Модель для создания нового продукта '''
class ProductCreate(ProductBase):
    pass


''' Модель для внесения изменений продукту '''
class ProductUpdate(BaseModel):
    name: str = Field(None, min_length=1, max_length=200, description='Название товара')
    description: Optional[str] = Field(None, max_length=2000, description='Описание товара')
    price: Decimal = Field(None, gt=0, description='Цена товара')
    grade: GradeEnum = Field(None, description='Grade модели')
    manufacturer: str = Field(None, min_length=1, max_length=100, description='Производитель')
    series: Optional[str] = Field(None, max_length=100, description='Серия')
    scale: Optional[str] = Field(None, max_length=20, description='Масштаб')
    difficulty: Optional[int] = Field(None, ge=1, le=5, description='Сложность (1-5)')
    in_stock: int = Field(None, ge=0, description='Количество в наличии')


''' Модель для отображения данных о продукте в ответе API '''
class ProductResponse(ProductBase):
    id: uuid.UUID
    main_image: Optional[str] = Field(None, description='Ссылка на основное изображение')
    additional_images: Optional[List[str]] = Field(None, description='Список дополнительных изображений')
    average_rating: Decimal = Field(default=Decimal('0.0'), description='Средний рейтинг (по умолчанию 0.0)')
    total_reviews: int = Field(default=0, description='Общее число отзывов')
    created_at: datetime = Field(..., description='Дата и время создания товара')
    updated_at: datetime = Field(..., description='Дата и время последнего обновления товара')

    ''' Берем информацию насчет продукта '''
    class Config:
        from_attributes = True


''' Модель для возвращения списка товаров с поддержкой пагинации '''
class ProductListResponse(BaseModel):
    items: List[ProductResponse] = Field(..., description='Список объектов типа (ProductResponse)')
    total: int = Field(..., description='Общее число элементов')
    page: int = Field(..., description='Текущая страница')
    per_page: int = Field(..., description='Количество товаров на странице')
    pages: int = Field(..., description='Общее количество страниц')


''' Модель для фильтрации продукта '''
class ProductFilter(BaseModel):
    search: Optional[str] = Field(None, description='Поиск по названию/описанию')
    grade: Optional[List[GradeEnum]] = Field(None, description='Фильтр по Grade')
    manufacturer: Optional[List[str]] = Field(None, description='Фильтр по производителям')
    series: Optional[List[str]] = Field(None, description='Фильтр по сериям')
    price_min: Optional[Decimal] = Field(None, ge=0, description='Минимальная цена')
    price_max: Optional[Decimal] = Field(None, ge=0, description='Максимальная цена')
    rating_min: Optional[Decimal] = Field(None, ge=0, le=5, description='Минимальный рейтинг')
    in_stock_only: Optional[bool] = Field(False, description='Только товары в наличии')
    sort_by: Optional[str] = Field('created_at', description='Сортировка')
    sort_order: Optional[str] = Field('desc', description='Порядок сортировки')

    ''' Поле, по которому происходит сортировка '''
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_sorts = ['created_at', 'price', 'name', 'average_rating', 'total_reviews']
        if v not in allowed_sorts:
            raise ValueError(f'Сортировка должна быть одной из: {", ".join(allowed_sorts)}')
        return v

    ''' Направление сортировки '''
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Порядок сортировки должен быть asc или desc')
        return v


''' Метод для ответа при загрузки изображения '''
class ProductImageUpload(BaseModel):
    filename: str = Field(..., description='Название загружаемого файла')
    url: str = Field(..., description='URL, по которому можно получить изображение')
    size: int = Field(..., description='Размер файла изображения в байтах')
