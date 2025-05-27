from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import math

from ..database import get_db
from ..services.review_service import ReviewService
from ..schemas import review as review_schemas
from ..utils.dependencies import get_current_user, get_current_admin_user
from ..models.user import User

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("/", response_model=review_schemas.Review)
async def create_review(
        review_data: review_schemas.ReviewCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создание нового отзыва"""
    return await ReviewService.create_review(db, review_data, current_user.id)


@router.get("/", response_model=review_schemas.ReviewList)
async def get_reviews(
        product_id: Optional[uuid.UUID] = Query(None, description="ID товара"),
        page: int = Query(1, ge=1, description="Номер страницы"),
        size: int = Query(10, ge=1, le=50, description="Количество элементов на странице"),
        rating_filter: Optional[int] = Query(None, ge=1, le=5, description="Фильтр по рейтингу"),
        db: Session = Depends(get_db)
):
    """Получение списка отзывов"""

    skip = (page - 1) * size
    reviews, total = await ReviewService.get_reviews(
        db=db,
        product_id=product_id,
        skip=skip,
        limit=size,
        rating_filter=rating_filter
    )

    pages = math.ceil(total / size)

    return review_schemas.ReviewList(
        reviews=reviews,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/my", response_model=review_schemas.ReviewList)
async def get_my_reviews(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получение отзывов текущего пользователя"""

    skip = (page - 1) * size
    reviews, total = await ReviewService.get_reviews(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=size,
        only_approved=False  # пользователь видит все свои отзывы
    )

    pages = math.ceil(total / size)

    return review_schemas.ReviewList(
        reviews=reviews,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{review_id}", response_model=review_schemas.Review)
async def get_review(
        review_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: Optional[User] = Depends(get_current_user)
):
    """Получение отзыва по ID"""

    current_user_id = current_user.id if current_user else None
    return await ReviewService.get_review_by_id(db, review_id, current_user_id)


@router.put("/{review_id}", response_model=review_schemas.Review)
async def update_review(
        review_id: uuid.UUID,
        review_data: review_schemas.ReviewUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновление отзыва"""

    return await ReviewService.update_review(
        db=db,
        review_id=review_id,
        review_data=review_data,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )


@router.delete("/{review_id}")
async def delete_review(
        review_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Удаление отзыва"""

    await ReviewService.delete_review(
        db=db,
        review_id=review_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )

    return {"message": "Отзыв успешно удален"}


@router.post("/{review_id}/images", response_model=review_schemas.Review)
async def add_review_images(
        review_id: uuid.UUID,
        images: List[UploadFile] = File(..., description="Изображения для отзыва (макс. 5)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Добавление изображений к отзыву"""

    if len(images) > 5:
        raise HTTPException(
            status_code=400,
            detail="Максимум 5 изображений за раз"
        )

    return await ReviewService.add_review_images(
        db=db,
        review_id=review_id,
        images=images,
        user_id=current_user.id
    )


@router.post("/{review_id}/helpful", response_model=review_schemas.ReviewHelpful)
async def vote_helpful(
        review_id: uuid.UUID,
        vote_data: review_schemas.ReviewHelpfulCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Голосование за полезность отзыва"""

    return await ReviewService.vote_helpful(
        db=db,
        review_id=review_id,
        user_id=current_user.id,
        is_helpful=vote_data.is_helpful
    )


@router.get("/stats/{product_id}", response_model=review_schemas.ReviewStats)
async def get_review_stats(
        product_id: uuid.UUID,
        db: Session = Depends(get_db)
):
    """Получение статистики отзывов для товара"""

    return await ReviewService.get_review_stats(db, product_id)


# Админские endpoints
@router.get("/admin/pending", response_model=review_schemas.ReviewList)
async def get_pending_reviews(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_admin_user)
):
    """Получение отзывов на модерацию (только для админов)"""

    skip = (page - 1) * size
    reviews, total = await ReviewService.get_reviews(
        db=db,
        skip=skip,
        limit=size,
        only_approved=False
    )

    # Фильтруем только неодобренные или скрытые
    pending_reviews = [r for r in reviews if not r.is_approved or r.is_hidden]

    pages = math.ceil(len(pending_reviews) / size)

    return review_schemas.ReviewList(
        reviews=pending_reviews,
        total=len(pending_reviews),
        page=page,
        size=size,
        pages=pages
    )


@router.patch("/admin/{review_id}/approve", response_model=review_schemas.Review)
async def approve_review(
        review_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_admin_user)
):
    """Одобрение отзыва (только для админов)"""

    update_data = review_schemas.ReviewUpdate(is_approved=True, is_hidden=False)
    return await ReviewService.update_review(
        db=db,
        review_id=review_id,
        review_data=update_data,
        user_id=current_admin.id,
        is_admin=True
    )


@router.patch("/admin/{review_id}/hide", response_model=review_schemas.Review)
async def hide_review(
        review_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_admin_user)
):
    """Скрытие отзыва (только для админов)"""

    update_data = review_schemas.ReviewUpdate(is_hidden=True)
    return await ReviewService.update_review(
        db=db,
        review_id=review_id,
        review_data=update_data,
        user_id=current_admin.id,
        is_admin=True
    )


@router.delete("/admin/{review_id}")
async def admin_delete_review(
        review_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_admin_user)
):
    """Удаление отзыва администратором"""

    await ReviewService.delete_review(
        db=db,
        review_id=review_id,
        user_id=current_admin.id,
        is_admin=True
    )

    return {"message": "Отзыв успешно удален администратором"}