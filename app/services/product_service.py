from typing import List, Optional, Tuple, Type
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func

from app.models import Product
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilter
from app.services.file_service import FileService
import math


class ProductService:

    @staticmethod
    def create_product(db: Session, product_data: ProductCreate) -> Product:
        """
        Создание нового товара

        Args:
            db: Сессия базы данных
            product_data: Данные для создания товара

        Returns:
            Product: Созданный товар
        """
        db_product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            grade=product_data.grade,
            manufacturer=product_data.manufacturer,
            series=product_data.series,
            scale=product_data.scale,
            difficulty=product_data.difficulty,
            in_stock=product_data.in_stock
        )

        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        return db_product

    @staticmethod
    def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
        """
        Получение товара по ID

        Args:
            db: Сессия базы данных
            product_id: ID товара

        Returns:
            Product: Товар или None если не найден
        """
        return db.query(Product).filter(product_id == Product.id).first()

    @staticmethod
    def update_product(db: Session, product_id: str, product_data: ProductUpdate) -> Optional[Product]:
        """
        Обновление товара

        Args:
            db: Сессия базы данных
            product_id: ID товара
            product_data: Данные для обновления

        Returns:
            Product: Обновленный товар или None если не найден
        """
        db_product = ProductService.get_product_by_id(db, product_id)
        if not db_product:
            return None

        # Обновляем только переданные поля
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)

        return db_product

    @staticmethod
    def delete_product(db: Session, product_id: str) -> bool:
        """
        Удаление товара

        Args:
            db: Сессия базы данных
            product_id: ID товара

        Returns:
            bool: True если товар удален, False если не найден
        """
        db_product = ProductService.get_product_by_id(db, product_id)
        if not db_product:
            return False

        # Удаляем изображения товара
        if db_product.main_image:
            FileService.delete_file(db_product.main_image)

        if db_product.additional_images:
            for image_path in db_product.additional_images:
                FileService.delete_file(image_path)

        db.delete(db_product)
        db.commit()

        return True

    @staticmethod
    def get_products_with_filters(
            db: Session,
            filters: ProductFilter,
            page: int = 1,
            per_page: int = 12
    ) -> Tuple[List[Product], int]:
        """
        Получение товаров с фильтрацией и пагинацией

        Args:
            db: Сессия базы данных
            filters: Фильтры для поиска
            page: Номер страницы
            per_page: Количество товаров на странице

        Returns:
            Tuple[List[Product], int]: Список товаров и общее количество
        """
        query = db.query(Product)

        # Применяем фильтры
        query = ProductService._apply_filters(query, filters)

        # Общее количество товаров (до пагинации)
        total = query.count()

        # Применяем сортировку
        query = ProductService._apply_sorting(query, filters.sort_by, filters.sort_order)

        # Применяем пагинацию
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()

        return products, total

    @staticmethod
    def _apply_filters(query, filters: ProductFilter):
        """Применение фильтров к запросу"""

        # Поиск по названию и описанию
        if filters.search:
            search_term = f"%{filters.search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Product.name).contains(search_term),
                    func.lower(Product.description).contains(search_term),
                    func.lower(Product.series).contains(search_term)
                )
            )

        # Фильтр по грейдам
        if filters.grade:
            query = query.filter(Product.grade.in_(filters.grade))

        # Фильтр по производителям
        if filters.manufacturer:
            query = query.filter(Product.manufacturer.in_(filters.manufacturer))

        # Фильтр по сериям
        if filters.series:
            query = query.filter(Product.series.in_(filters.series))

        # Фильтр по цене
        if filters.price_min is not None:
            query = query.filter(Product.price >= filters.price_min)

        if filters.price_max is not None:
            query = query.filter(Product.price <= filters.price_max)

        # Фильтр по рейтингу
        if filters.rating_min is not None:
            query = query.filter(Product.average_rating >= filters.rating_min)

        # Только товары в наличии
        if filters.in_stock_only:
            query = query.filter(Product.in_stock > 0)

        return query

    @staticmethod
    def _apply_sorting(query, sort_by: str, sort_order: str):
        """Применение сортировки к запросу"""

        # Определяем поле для сортировки
        sort_field = getattr(Product, sort_by, Product.created_at)

        # Применяем сортировку
        if sort_order == 'desc':
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))

        return query

    @staticmethod
    def update_product_images(
            db: Session,
            product_id: str,
            main_image: Optional[str] = None,
            additional_images: Optional[List[str]] = None
    ) -> Optional[Product]:
        """
        Обновление изображений товара

        Args:
            db: Сессия базы данных
            product_id: ID товара
            main_image: Путь к основному изображению
            additional_images: Список путей к дополнительным изображениям

        Returns:
            Product: Обновленный товар или None если не найден
        """
        db_product = ProductService.get_product_by_id(db, product_id)
        if not db_product:
            return None

        # Обновляем основное изображение
        if main_image is not None:
            # Удаляем старое изображение
            if db_product.main_image:
                FileService.delete_file(db_product.main_image)
            db_product.main_image = main_image

        # Обновляем дополнительные изображения
        if additional_images is not None:
            # Удаляем старые изображения
            if db_product.additional_images:
                for image_path in db_product.additional_images:
                    FileService.delete_file(image_path)
            db_product.additional_images = additional_images

        db.commit()
        db.refresh(db_product)

        return db_product

    @staticmethod
    def get_product_filters_data(db: Session) -> dict:
        """
        Получение данных для фильтров (уникальные значения)

        Args:
            db: Сессия базы данных

        Returns:
            dict: Данные для фильтров
        """
        # Получаем уникальные производители
        manufacturers = db.query(Product.manufacturer).distinct().all()
        manufacturers = [m[0] for m in manufacturers if m[0]]

        # Получаем уникальные серии
        series = db.query(Product.series).distinct().all()
        series = [s[0] for s in series if s[0]]

        # Получаем диапазон цен
        price_range = db.query(
            func.min(Product.price),
            func.max(Product.price)
        ).first()

        return {
            "manufacturers": sorted(manufacturers),
            "series": sorted(series),
            "price_min": float(price_range[0]) if price_range[0] else 0,
            "price_max": float(price_range[1]) if price_range[1] else 0,
            "grades": [grade.value for grade in Product.grade.type.enums]
        }

    @staticmethod
    def get_featured_products(db: Session, limit: int = 8) -> list[Type[Product]]:
        """
        Получение рекомендуемых товаров (по рейтингу и популярности)

        Args:
            db: Сессия базы данных
            limit: Количество товаров

        Returns:
            List[Product]: Список рекомендуемых товаров
        """
        return db.query(Product) \
            .filter(Product.in_stock > 0) \
            .order_by(desc(Product.average_rating), desc(Product.total_reviews)) \
            .limit(limit) \
            .all()

    @staticmethod
    def get_latest_products(db: Session, limit: int = 8) -> list[Type[Product]]:
        """
        Получение новых товаров

        Args:
            db: Сессия базы данных
            limit: Количество товаров

        Returns:
            List[Product]: Список новых товаров
        """
        return db.query(Product) \
            .order_by(desc(Product.created_at)) \
            .limit(limit) \
            .all()