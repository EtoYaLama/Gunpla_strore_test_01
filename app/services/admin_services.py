from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_
from decimal import Decimal

from ..models.user import User
from ..models.product import Product
from ..models.order import Order, OrderItem
from ..models.review import Review
from ..schemas.user import UserUpdate, UserCreate
from ..schemas.product import ProductCreate, ProductUpdate
from ..utils.exceptions import AdminServiceException


class AdminService:
    """Сервис для административных функций"""

    def __init__(self, db: Session):
        self.db = db

    # === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===

    def get_users_stats(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        try:
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            admin_users = self.db.query(User).filter(User.is_admin == True).count()

            # Пользователи за последний месяц
            month_ago = datetime.utcnow() - timedelta(days=30)
            new_users_month = self.db.query(User).filter(
                User.created_at >= month_ago
            ).count()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "new_users_month": new_users_month,
                "inactive_users": total_users - active_users
            }
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения статистики пользователей: {str(e)}")

    def get_all_users(self, skip: int = 0, limit: int = 50,
                      search: Optional[str] = None) -> List[User]:
        """Получить список всех пользователей с поиском"""
        try:
            query = self.db.query(User)

            if search:
                query = query.filter(
                    or_(
                        User.username.ilike(f"%{search}%"),
                        User.email.ilike(f"%{search}%"),
                        User.full_name.ilike(f"%{search}%")
                    )
                )

            return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения пользователей: {str(e)}")

    def toggle_user_status(self, user_id: str) -> User:
        """Активировать/деактивировать пользователя"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise AdminServiceException("Пользователь не найден")

            user.is_active = not user.is_active
            user.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка изменения статуса пользователя: {str(e)}")

    def make_admin(self, user_id: str) -> User:
        """Сделать пользователя администратором"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise AdminServiceException("Пользователь не найден")

            user.is_admin = True
            user.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка назначения администратора: {str(e)}")

    # === УПРАВЛЕНИЕ ТОВАРАМИ ===

    def get_products_stats(self) -> Dict[str, Any]:
        """Получить статистику товаров"""
        try:
            total_products = self.db.query(Product).count()
            in_stock = self.db.query(Product).filter(Product.in_stock > 0).count()
            out_of_stock = self.db.query(Product).filter(Product.in_stock == 0).count()

            # Самые популярные товары (по количеству заказов)
            popular_products = self.db.query(
                Product.name,
                func.sum(OrderItem.quantity).label('total_sold')
            ).join(OrderItem).group_by(Product.id, Product.name) \
                .order_by(desc('total_sold')).limit(5).all()

            # Средняя цена товаров
            avg_price = self.db.query(func.avg(Product.price)).scalar() or 0

            return {
                "total_products": total_products,
                "in_stock": in_stock,
                "out_of_stock": out_of_stock,
                "avg_price": float(avg_price),
                "popular_products": [
                    {"name": name, "sold": int(sold)}
                    for name, sold in popular_products
                ]
            }
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения статистики товаров: {str(e)}")

    def create_product(self, product_data: ProductCreate) -> Product:
        """Создать новый товар"""
        try:
            product = Product(**product_data.dict())
            product.created_at = datetime.utcnow()
            product.updated_at = datetime.utcnow()

            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка создания товара: {str(e)}")

    def update_product(self, product_id: str, product_data: ProductUpdate) -> Product:
        """Обновить товар"""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise AdminServiceException("Товар не найден")

            update_data = product_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(product, field, value)

            product.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка обновления товара: {str(e)}")

    def delete_product(self, product_id: str) -> bool:
        """Удалить товар"""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise AdminServiceException("Товар не найден")

            # Проверим, есть ли активные заказы с этим товаром
            active_orders = self.db.query(OrderItem).join(Order).filter(
                and_(
                    OrderItem.product_id == product_id,
                    Order.status.in_(["pending", "confirmed", "shipped"])
                )
            ).count()

            if active_orders > 0:
                raise AdminServiceException(
                    "Нельзя удалить товар с активными заказами. "
                    "Дождитесь завершения всех заказов."
                )

            self.db.delete(product)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка удаления товара: {str(e)}")

    def update_product_stock(self, product_id: str, new_stock: int) -> Product:
        """Обновить остатки товара"""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise AdminServiceException("Товар не найден")

            product.in_stock = new_stock
            product.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка обновления остатков: {str(e)}")

    # === УПРАВЛЕНИЕ ЗАКАЗАМИ ===

    def get_orders_stats(self) -> Dict[str, Any]:
        """Получить статистику заказов"""
        try:
            total_orders = self.db.query(Order).count()
            pending_orders = self.db.query(Order).filter(Order.status == "pending").count()
            completed_orders = self.db.query(Order).filter(Order.status == "delivered").count()

            # Общий доход
            total_revenue = self.db.query(func.sum(Order.total_amount)).filter(
                Order.status == "delivered"
            ).scalar() or 0

            # Доход за месяц
            month_ago = datetime.utcnow() - timedelta(days=30)
            month_revenue = self.db.query(func.sum(Order.total_amount)).filter(
                and_(
                    Order.status == "delivered",
                    Order.created_at >= month_ago
                )
            ).scalar() or 0

            # Средний чек
            avg_order_value = self.db.query(func.avg(Order.total_amount)).filter(
                Order.status == "delivered"
            ).scalar() or 0

            return {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
                "total_revenue": float(total_revenue),
                "month_revenue": float(month_revenue),
                "avg_order_value": float(avg_order_value)
            }
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения статистики заказов: {str(e)}")

    def get_all_orders(self, skip: int = 0, limit: int = 50,
                       status: Optional[str] = None) -> List[Order]:
        """Получить все заказы с фильтрацией по статусу"""
        try:
            query = self.db.query(Order)

            if status:
                query = query.filter(Order.status == status)

            return query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения заказов: {str(e)}")

    def update_order_status(self, order_id: str, new_status: str) -> Order:
        """Обновить статус заказа"""
        try:
            allowed_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
            if new_status not in allowed_statuses:
                raise AdminServiceException(f"Недопустимый статус: {new_status}")

            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise AdminServiceException("Заказ не найден")

            order.status = new_status
            order.updated_at = datetime.utcnow()

            # Если заказ доставлен, устанавливаем дату доставки
            if new_status == "delivered":
                order.estimated_delivery = datetime.utcnow()

            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка обновления статуса заказа: {str(e)}")

    # === УПРАВЛЕНИЕ ОТЗЫВАМИ ===

    def get_reviews_stats(self) -> Dict[str, Any]:
        """Получить статистику отзывов"""
        try:
            total_reviews = self.db.query(Review).count()

            # Распределение по рейтингам
            rating_distribution = {}
            for rating in range(1, 6):
                count = self.db.query(Review).filter(Review.rating == rating).count()
                rating_distribution[f"rating_{rating}"] = count

            # Средний рейтинг
            avg_rating = self.db.query(func.avg(Review.rating)).scalar() or 0

            # Отзывы за месяц
            month_ago = datetime.utcnow() - timedelta(days=30)
            month_reviews = self.db.query(Review).filter(
                Review.created_at >= month_ago
            ).count()

            return {
                "total_reviews": total_reviews,
                "avg_rating": float(avg_rating),
                "month_reviews": month_reviews,
                **rating_distribution
            }
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения статистики отзывов: {str(e)}")

    def get_all_reviews(self, skip: int = 0, limit: int = 50) -> List[Review]:
        """Получить все отзывы"""
        try:
            return self.db.query(Review).order_by(desc(Review.created_at)) \
                .offset(skip).limit(limit).all()
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения отзывов: {str(e)}")

    def delete_review(self, review_id: str) -> bool:
        """Удалить отзыв (модерация)"""
        try:
            review = self.db.query(Review).filter(Review.id == review_id).first()
            if not review:
                raise AdminServiceException("Отзыв не найден")

            self.db.delete(review)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise AdminServiceException(f"Ошибка удаления отзыва: {str(e)}")

    # === ОБЩАЯ АНАЛИТИКА ===

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получить общую статистику для дашборда"""
        try:
            return {
                "users": self.get_users_stats(),
                "products": self.get_products_stats(),
                "orders": self.get_orders_stats(),
                "reviews": self.get_reviews_stats()
            }
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения статистики дашборда: {str(e)}")

    def get_sales_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Получить аналитику продаж за указанный период"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Продажи по дням
            daily_sales = self.db.query(
                func.date(Order.created_at).label('date'),
                func.sum(Order.total_amount).label('revenue'),
                func.count(Order.id).label('orders_count')
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.status == "delivered"
                )
            ).group_by(func.date(Order.created_at)) \
                .order_by('date').all()

            # Топ товары
            top_products = self.db.query(
                Product.name,
                func.sum(OrderItem.quantity).label('total_sold'),
                func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
            ).join(OrderItem).join(Order).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.status == "delivered"
                )
            ).group_by(Product.id, Product.name) \
                .order_by(desc('total_sold')).limit(10).all()

            return {
                "period_days": days,
                "daily_sales": [
                    {
                        "date": str(date),
                        "revenue": float(revenue or 0),
                        "orders_count": orders_count or 0
                    }
                    for date, revenue, orders_count in daily_sales
                ],
                "top_products": [
                    {
                        "name": name,
                        "sold": int(sold or 0),
                        "revenue": float(revenue or 0)
                    }
                    for name, sold, revenue in top_products
                ]
            }
        except Exception as e:
            raise AdminServiceException(f"Ошибка получения аналитики продаж: {str(e)}")