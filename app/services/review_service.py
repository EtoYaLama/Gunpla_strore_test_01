from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Type
from fastapi import HTTPException, UploadFile
import uuid
import os
from PIL import Image
import aiofiles

from app.models import Product, Review, ReviewHelpful
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewStats


class ReviewService:

    @staticmethod
    async def create_review(
            db: Session,
            review_data: 'ReviewCreate',
            user_id: uuid.UUID
    ) -> Review:
        """ Создание нового отзыва """

        # Проверяем, не оставлял ли пользователь уже отзыв на этот товар
        existing_review = db.query(Review).filter(
            and_(Review.user_id == user_id, Review.product_id == review_data.product_id)
        ).first()

        if existing_review:
            raise HTTPException(
                status_code=400,
                detail="Вы уже оставили отзыв на этот товар"
            )

        ''' Проверяем существование товара '''
        product = db.query(Product).filter(and_(review_data.product_id == Product.id)).first()

        if not product:
            raise HTTPException(status_code=404, detail='Товар не найден')

        review = Review(
            user_id=user_id,
            product_id=review_data.product_id,
            rating=review_data.rating,
            comment=review_data.comment
        )

        db.add(review)
        db.commit()
        db.refresh(review)

        ''' Обновляем рейтинг товара '''
        await ReviewService.update_product_rating(db, review_data.product_id)

        return review

    @staticmethod
    async def get_reviews(
            db: Session,
            product_id: Optional[uuid.UUID] = None,
            user_id: Optional[uuid.UUID] = None,
            skip: int = 0,
            limit: int = 20,
            rating_filter: Optional[int] = None,
            only_approved: bool = True
    ) -> tuple[int, list[Type[Review]]]:
        """Получение списка отзывов с фильтрами"""

        query = db.query(Review)

        ''' Фильтры '''
        if product_id:
            query = query.filter(product_id == Review.product_id)

        if user_id:
            query = query.filter(user_id == Review.user_id)

        if rating_filter:
            query = query.filter(rating_filter == Review.rating)

        if only_approved:
            query = query.filter(and_(Review.is_approved == True, Review.is_hidden == False))

        ''' Подсчет общего количества '''
        total = query.count()

        ''' Получение отзывов с пагинацией '''
        reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

        return total, reviews

    @staticmethod
    async def get_review_by_id(
            db: Session,
            review_id: uuid.UUID,
            current_user_id: Optional[uuid.UUID] = None
    ) -> Type[Review]:
        """ Получение отзыва по ID с дополнительной информацией """

        review = db.query(Review).filter(review_id == Review.id).first()
        if not review:
            raise HTTPException(status_code=404, detail='Отзыв не найден')

        ''' Добавляем информацию о голосах за полезность '''
        if current_user_id:
            helpful_vote = db.query(ReviewHelpful).filter(
                and_(
                    ReviewHelpful.review_id == review_id,
                    ReviewHelpful.user_id == current_user_id
                )
            ).first()
            review.user_helpful_vote = helpful_vote.is_helpful if helpful_vote else None

        ''' Подсчитываем голоса за полезность '''
        helpful_stats = db.query(
            func.sum(func.case([(ReviewHelpful.is_helpful == True, 1)], else_=0)).label('helpful'),
            func.sum(func.case([(ReviewHelpful.is_helpful == False, 1)], else_=0)).label('not_helpful')
        ).filter(review_id == ReviewHelpful.review_id).first()

        review.helpful_count = helpful_stats.helpful or 0
        review.not_helpful_count = helpful_stats.not_helpful or 0

        return review

    @staticmethod
    async def update_review(
            db: Session,
            review_id: uuid.UUID,
            review_data: 'ReviewUpdate',
            user_id: uuid.UUID,
            is_admin: bool = False
    ) -> Type[Review]:
        """ Обновление отзыва """

        review = db.query(Review).filter(review_id == Review.id).first()
        if not review:
            raise HTTPException(status_code=404, detail='Отзыв не найден')

        ''' Проверяем права на редактирование '''
        if not is_admin and review.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail='Нет прав на редактирование этого отзыва'
            )

        ''' Обновляем поля '''
        update_data = review_data.dict(exclude_unset=True)

        ''' Обычные пользователи могут менять только rating и comment '''
        if not is_admin:
            update_data = {k: v for k, v in update_data.items() if k in ['rating', 'comment']}

        for field, value in update_data.items():
            setattr(review, field, value)

        db.commit()
        db.refresh(review)

        ''' Обновляем рейтинг товара если изменился rating '''
        if 'rating' in update_data:
            await ReviewService.update_product_rating(db, review.product_id)

        return review

    @staticmethod
    async def delete_review(
            db: Session,
            review_id: uuid.UUID,
            user_id: uuid.UUID,
            is_admin: bool = False
    ) -> bool:
        """ Удаление отзыва """

        review = db.query(Review).filter(review_id == Review.id).first()
        if not review:
            raise HTTPException(status_code=404, detail='Отзыв не найден')

        ''' Проверяем права на удаление '''
        if not is_admin and review.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail='Нет прав на удаление этого отзыва'
            )

        product_id = review.product_id

        ''' Удаляем изображения '''
        if review.images:
            for image_path in review.images:
                try:
                    if os.path.exists(f'static/{image_path}'):
                        os.remove(f'static/{image_path}')
                except Exception:
                    pass

        db.delete(review)
        db.commit()

        ''' Обновляем рейтинг товара '''
        await ReviewService.update_product_rating(db, product_id)

        return True

    @staticmethod
    async def add_review_images(
            db: Session,
            review_id: uuid.UUID,
            images: List[UploadFile],
            user_id: uuid.UUID
    ) -> Type[Review]:
        """ Добавление изображений к отзыву """

        review = db.query(Review).filter(review_id == Review.id).first()
        if not review:
            raise HTTPException(status_code=404, detail='Отзыв не найден')

        if review.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail='Нет прав на редактирование этого отзыва'
            )

        ''' Проверяем лимит изображений (максимум 5) '''
        current_images = review.images or []
        if len(current_images) + len(images) > 5:
            raise HTTPException(
                status_code=400,
                detail='Максимум 5 изображений на отзыв'
            )

        new_images = []
        upload_dir = f"static/uploads/reviews/{review_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for image in images:
            ''' Проверяем тип файла '''
            if not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f'Файл {image.filename} не является изображением'
                )

            ''' Генерируем уникальное имя файла '''
            file_extension = image.filename.split('.')[-1].lower()
            filename = f'{uuid.uuid4()}.{file_extension}'
            file_path = f'{upload_dir}/{filename}'

            ''' Сохраняем файл '''
            async with aiofiles.open(file_path, 'wb') as f:
                content = await image.read()
                await f.write(content)

            ''' Сжимаем изображение '''
            try:
                with Image.open(file_path) as img:
                    # Конвертируем в RGB если нужно
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')

                    ''' Ресайзим если слишком большое '''
                    max_size = (800, 600)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                    ''' Сохраняем с оптимизацией '''
                    img.save(file_path, optimize=True, quality=85)
            except Exception:
                ''' Удаляем файл если не удалось обработать '''
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка обработки изображения {image.filename}"
                )

            new_images.append(f'uploads/reviews/{review_id}/{filename}')

        ''' Обновляем список изображений в отзыве '''
        review.images = current_images + new_images
        db.commit()
        db.refresh(review)

        return review

    @staticmethod
    async def vote_helpful(
            db: Session,
            review_id: uuid.UUID,
            user_id: uuid.UUID,
            is_helpful: bool
    ) -> Type[ReviewHelpful] | ReviewHelpful:
        """ Голосование за полезность отзыва """

        ''' Проверяем существование отзыва '''
        review = db.query(Review).filter(review_id == Review.id).first()
        if not review:
            raise HTTPException(status_code=404, detail='Отзыв не найден')

        # Проверяем, не голосовал ли пользователь уже
        existing_vote = db.query(ReviewHelpful).filter(
            and_(
                ReviewHelpful.review_id == review_id,
                ReviewHelpful.user_id == user_id
            )
        ).first()

        if existing_vote:
            ''' Обновляем существующий голос '''
            existing_vote.is_helpful = is_helpful
            db.commit()
            db.refresh(existing_vote)
            return existing_vote
        else:
            ''' Создаем новый голос '''
            vote = ReviewHelpful(
                review_id=review_id,
                user_id=user_id,
                is_helpful=is_helpful
            )
            db.add(vote)
            db.commit()
            db.refresh(vote)
            return vote

    @staticmethod
    async def get_review_stats(db: Session, product_id: uuid.UUID) -> ReviewStats:
        """ Получение статистики отзывов для товара """

        ''' Получаем все одобренные отзывы товара '''
        reviews = db.query(ReviewStats).filter(
            and_(
                Review.product_id == product_id,
                Review.is_approved == True,
                Review.is_hidden == False
            )
        ).all()

        if not reviews:
            return Review.ReviewStats(
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            )

        ''' Подсчитываем статистику '''
        total_reviews = len(reviews)
        total_rating = sum(review.rating for review in reviews)
        average_rating = round(total_rating / total_reviews, 1)

        ''' Распределение по рейтингам '''
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[review.rating] += 1

        return review_schemas.ReviewStats(
            total_reviews=total_reviews,
            average_rating=average_rating,
            rating_distribution=rating_distribution
        )

    @staticmethod
    async def update_product_rating(db: Session, product_id: uuid.UUID):
        """ Обновление рейтинга товара """

        stats = await ReviewService.get_review_stats(db, product_id)

        ''' Обновляем поля в товаре '''
        product = db.query(Product).filter(product_id == Product.id).first()
        if product:
            product.average_rating = stats.average_rating
            product.total_reviews = stats.total_reviews
            db.commit()