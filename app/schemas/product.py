from pydantic import BaseModel, validator, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid
from app.models.product import GradeEnum


# Базовые схемы
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Название товара")
    description: Optional[str] = Field(None, max_length=2000, description="Описание товара")
    price: Decimal = Field(..., gt=0, description="Цена товара")
    grade: GradeEnum = Field(..., description="Грейд модели")
    manufacturer: str = Field(..., min_length=1, max_length=100, description="Производитель")
    series: Optional[str] = Field(None, max_length=100, description="Серия")
    scale: Optional[str] = Field(None, max_length=20, description="Масштаб")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Сложность (1-5)")
    in_stock: int = Field(default=0, ge=0, description="Количество в наличии")


class ProductCreate(ProductBase):
    """Схема для создания товара"""
    pass


class ProductUpdate(BaseModel):
    """Схема для обновления товара"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0)
    grade: Optional[GradeEnum] = None
    manufacturer: Optional[str] = Field(None, min_length=1, max_length=100)
    series: Optional[str] = Field(None, max_length=100)
    scale: Optional[str] = Field(None, max_length=20)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    in_stock: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    """Схема для ответа с товаром"""
    id: uuid.UUID
    main_image: Optional[str] = None
    additional_images: Optional[List[str]] = []
    average_rating: Decimal = Field(default=Decimal('0.0'))
    total_reviews: int = Field(default=0)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Схема для списка товаров с пагинацией"""
    items: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ProductFilter(BaseModel):
    """Схема для фильтрации товаров"""
    search: Optional[str] = Field(None, description="Поиск по названию/описанию")
    grade: Optional[List[GradeEnum]] = Field(None, description="Фильтр по грейдам")
    manufacturer: Optional[List[str]] = Field(None, description="Фильтр по производителям")
    series: Optional[List[str]] = Field(None, description="Фильтр по сериям")
    price_min: Optional[Decimal] = Field(None, ge=0, description="Минимальная цена")
    price_max: Optional[Decimal] = Field(None, ge=0, description="Максимальная цена")
    rating_min: Optional[Decimal] = Field(None, ge=0, le=5, description="Минимальный рейтинг")
    in_stock_only: Optional[bool] = Field(False, description="Только товары в наличии")
    sort_by: Optional[str] = Field("created_at", description="Сортировка")
    sort_order: Optional[str] = Field("desc", description="Порядок сортировки")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_sorts = ['created_at', 'price', 'name', 'average_rating', 'total_reviews']
        if v not in allowed_sorts:
            raise ValueError(f'Сортировка должна быть одной из: {", ".join(allowed_sorts)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Порядок сортировки должен быть asc или desc')
        return v


class ProductImageUpload(BaseModel):
    """Схема для ответа после загрузки изображения"""
    filename: str
    url: str
    size: int