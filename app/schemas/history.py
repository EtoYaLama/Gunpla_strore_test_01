from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List

from app.schemas.product import ProductBase


class ViewHistoryBase(BaseModel):
    user_id: UUID4
    product_id: UUID4


class ViewHistoryCreate(ViewHistoryBase):
    pass


class ViewHistoryResponse(ViewHistoryBase):
    id: UUID4
    viewed_at: datetime
    product: Optional[ProductBase] = None

    class Config:
        from_attributes = True


class ViewHistoryList(BaseModel):
    items: List[ViewHistoryResponse]
    total: int
    page: int
    size: int
    pages: int


class FavoritesBase(BaseModel):
    user_id: UUID4
    product_id: UUID4


class FavoritesCreate(BaseModel):
    product_id: UUID4


class FavoritesResponse(FavoritesBase):
    id: UUID4
    created_at: datetime
    product: Optional[ProductBase] = None

    class Config:
        from_attributes = True


class FavoritesList(BaseModel):
    items: List[FavoritesResponse]
    total: int
    page: int
    size: int
    pages: int


class FavoritesToggleResponse(BaseModel):
    is_favorite: bool
    message: str


# Дополнительные схемы для продуктов с информацией об избранном
class ProductWithFavoriteStatus(ProductBase):
    is_favorite: bool = False

    class Config:
        from_attributes = True