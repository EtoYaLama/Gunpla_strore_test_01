from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import math

from app.database import get_db
from app.schemas.history import (
    ViewHistoryResponse, ViewHistoryList,
    FavoritesResponse, FavoritesList, FavoritesCreate,
    FavoritesToggleResponse
)
from app.services.history_service import HistoryService, FavoritesService
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/history", tags=["history"])
favorites_router = APIRouter(prefix="/favorites", tags=["favorites"])


# История просмотров
@router.post("/view/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_view_history(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Добавляет товар в историю просмотров пользователя.
    """
    try:
        view_record = HistoryService.add_view_history(
            db=db,
            user_id=current_user.id,
            product_id=product_id
        )
        return {"message": "Просмотр записан", "id": str(view_record.id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при записи просмотра: {str(e)}"
        )


@router.get("/", response_model=ViewHistoryList)
async def get_user_history(
        page: int = Query(1, ge=1, description="Номер страницы"),
        size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получает историю просмотров текущего пользователя.
    """
    try:
        items, total = HistoryService.get_user_history(
            db=db,
            user_id=current_user.id,
            page=page,
            size=size
        )

        pages = math.ceil(total / size)

        return ViewHistoryList(
            items=[ViewHistoryResponse.from_orm(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении истории: {str(e)}"
        )


@router.get("/popular")
async def get_popular_products(
        days: int = Query(7, ge=1, le=365, description="Количество дней для анализа"),
        limit: int = Query(10, ge=1, le=50, description="Количество товаров"),
        db: Session = Depends(get_db)
):
    """
    Получает популярные товары на основе истории просмотров.
    """
    try:
        popular_products = HistoryService.get_popular_products(
            db=db,
            days=days,
            limit=limit
        )
        return {"popular_products": popular_products}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении популярных товаров: {str(e)}"
        )


# Избранные товары
@favorites_router.post("/toggle/{product_id}", response_model=FavoritesToggleResponse)
async def toggle_favorite(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Переключает товар в избранном (добавляет/удаляет).
    """
    try:
        result = FavoritesService.toggle_favorite(
            db=db,
            user_id=current_user.id,
            product_id=product_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при изменении избранного: {str(e)}"
        )


@favorites_router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Добавляет товар в избранное.
    """
    try:
        favorite = FavoritesService.add_to_favorites(
            db=db,
            user_id=current_user.id,
            product_id=product_id
        )
        return {"message": "Товар добавлен в избранное", "id": str(favorite.id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении в избранное: {str(e)}"
        )


@favorites_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Удаляет товар из избранного.
    """
    try:
        removed = FavoritesService.remove_from_favorites(
            db=db,
            user_id=current_user.id,
            product_id=product_id
        )
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден в избранном"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении из избранного: {str(e)}"
        )


@favorites_router.get("/", response_model=FavoritesList)
async def get_user_favorites(
        page: int = Query(1, ge=1, description="Номер страницы"),
        size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получает избранные товары текущего пользователя.
    """
    try:
        items, total = FavoritesService.get_user_favorites(
            db=db,
            user_id=current_user.id,
            page=page,
            size=size
        )

        pages = math.ceil(total / size)

        return FavoritesList(
            items=[FavoritesResponse.from_orm(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении избранного: {str(e)}"
        )


@favorites_router.get("/check/{product_id}")
async def check_favorite_status(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Проверяет, находится ли товар в избранном у пользователя.
    """
    try:
        is_favorite = FavoritesService.is_favorite(
            db=db,
            user_id=current_user.id,
            product_id=product_id
        )
        return {"is_favorite": is_favorite}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при проверке статуса избранного: {str(e)}"
        )


@favorites_router.get("/count")
async def get_favorites_count(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получает количество избранных товаров у пользователя.
    """
    try:
        count = FavoritesService.get_favorites_count(
            db=db,
            user_id=current_user.id
        )
        return {"count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении количества избранного: {str(e)}"
        )


# Объединяем роутеры
def include_routers(main_router):
    """
    Функция для включения роутеров в основное приложение.
    """
    main_router.include_router(router)
    main_router.include_router(favorites_router)