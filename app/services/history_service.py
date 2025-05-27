from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from app.models.history import ViewHistory, Favorites
from app.models.product import Product
from app.schemas.history import (
    ViewHistoryCreate, ViewHistoryResponse,
    FavoritesCreate, FavoritesResponse,
    FavoritesToggleResponse
)


class HistoryService:

    @staticmethod
    def add_view_history(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> Optional[ViewHistory]:
        """
        Добавляет запись о просмотре товара.
        Если товар уже просматривался в течение последних 10 минут - не добавляем дубликат.
        """
        # Проверяем, не было ли недавнего просмотра
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
        recent_view = db.query(ViewHistory).filter(
            and_(
                ViewHistory.user_id == user_id,
                ViewHistory.product_id == product_id,
                ViewHistory.viewed_at > ten_minutes_ago
            )
        ).first()

        if recent_view:
            # Обновляем время последнего просмотра
            recent_view.viewed_at = datetime.utcnow()
            db.commit()
            db.refresh(recent_view)
            return recent_view

        # Создаем новую запись
        view_record = ViewHistory(
            user_id=user_id,
            product_id=product_id,
            viewed_at=datetime.utcnow()
        )
        db.add(view_record)
        db.commit()
        db.refresh(view_record)
        return view_record

    @staticmethod
    def get_user_history(
            db: Session,
            user_id: uuid.UUID,
            page: int = 1,
            size: int = 20
    ) -> Tuple[List[ViewHistory], int]:
        """
        Получает историю просмотров пользователя с пагинацией.
        Группирует по товарам и показывает последний просмотр.
        """
        # Подзапрос для получения последнего просмотра каждого товара
        subquery = db.query(
            ViewHistory.product_id,
            func.max(ViewHistory.viewed_at).label('last_viewed')
        ).filter(
            ViewHistory.user_id == user_id
        ).group_by(ViewHistory.product_id).subquery()

        # Основной запрос
        query = db.query(ViewHistory).join(
            subquery,
            and_(
                ViewHistory.product_id == subquery.c.product_id,
                ViewHistory.viewed_at == subquery.c.last_viewed,
                ViewHistory.user_id == user_id
            )
        ).order_by(desc(ViewHistory.viewed_at))

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return items, total

    @staticmethod
    def get_popular_products(db: Session, days: int = 7, limit: int = 10) -> List[dict]:
        """
        Получает популярные товары на основе истории просмотров.
        """
        date_threshold = datetime.utcnow() - timedelta(days=days)

        popular_products = db.query(
            ViewHistory.product_id,
            func.count(ViewHistory.id).label('view_count'),
            func.count(func.distinct(ViewHistory.user_id)).label('unique_viewers')
        ).filter(
            ViewHistory.viewed_at > date_threshold
        ).group_by(
            ViewHistory.product_id
        ).order_by(
            desc('view_count')
        ).limit(limit).all()

        return [
            {
                'product_id': str(item.product_id),
                'view_count': item.view_count,
                'unique_viewers': item.unique_viewers
            }
            for item in popular_products
        ]

    @staticmethod
    def clear_old_history(db: Session, days: int = 90) -> int:
        """
        Очищает старую историю просмотров (старше указанного количества дней).
        """
        date_threshold = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(ViewHistory).filter(
            ViewHistory.viewed_at < date_threshold
        ).delete()
        db.commit()
        return deleted_count


class FavoritesService:

    @staticmethod
    def toggle_favorite(
            db: Session,
            user_id: uuid.UUID,
            product_id: uuid.UUID
    ) -> FavoritesToggleResponse:
        """
        Переключает товар в избранном (добавляет или удаляет).
        """
        # Проверяем, есть ли товар в избранном
        existing_favorite = db.query(Favorites).filter(
            and_(
                Favorites.user_id == user_id,
                Favorites.product_id == product_id
            )
        ).first()

        if existing_favorite:
            # Удаляем из избранного
            db.delete(existing_favorite)
            db.commit()
            return FavoritesToggleResponse(
                is_favorite=False,
                message="Товар удален из избранного"
            )
        else:
            # Добавляем в избранное
            favorite = Favorites(
                user_id=user_id,
                product_id=product_id
            )
            db.add(favorite)
            db.commit()
            return FavoritesToggleResponse(
                is_favorite=True,
                message="Товар добавлен в избранное"
            )

    @staticmethod
    def add_to_favorites(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> Optional[Favorites]:
        """
        Добавляет товар в избранное.
        """
        # Проверяем, не добавлен ли уже
        existing = db.query(Favorites).filter(
            and_(
                Favorites.user_id == user_id,
                Favorites.product_id == product_id
            )
        ).first()

        if existing:
            return existing

        favorite = Favorites(
            user_id=user_id,
            product_id=product_id
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite

    @staticmethod
    def remove_from_favorites(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
        """
        Удаляет товар из избранного.
        """
        favorite = db.query(Favorites).filter(
            and_(
                Favorites.user_id == user_id,
                Favorites.product_id == product_id
            )
        ).first()

        if favorite:
            db.delete(favorite)
            db.commit()
            return True
        return False

    @staticmethod
    def get_user_favorites(
            db: Session,
            user_id: uuid.UUID,
            page: int = 1,
            size: int = 20
    ) -> Tuple[List[Favorites], int]:
        """
        Получает избранные товары пользователя с пагинацией.
        """
        query = db.query(Favorites).filter(
            Favorites.user_id == user_id
        ).order_by(desc(Favorites.created_at))

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return items, total

    @staticmethod
    def is_favorite(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
        """
        Проверяет, находится ли товар в избранном у пользователя.
        """
        favorite = db.query(Favorites).filter(
            and_(
                Favorites.user_id == user_id,
                Favorites.product_id == product_id
            )
        ).first()

        return favorite is not None

    @staticmethod
    def get_favorites_count(db: Session, user_id: uuid.UUID) -> int:
        """
        Получает количество избранных товаров у пользователя.
        """
        return db.query(Favorites).filter(
            Favorites.user_id == user_id
        ).count()