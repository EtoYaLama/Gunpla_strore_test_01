from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session

from app.services.admin_services import AdminService
from app.services.auth_service import get_current_admin_user
from app.models import User, Review
from app.schemas.user import UserResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.utils.exceptions import AdminServiceException
from app.schemas.order import OrderResponse
from app.database import get_db  # Импорт зависимости для получения Session

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """Фабричная функция для создания AdminService"""
    return AdminService(db)


# === API ENDPOINTS ===

# === СТАТИСТИКА ===

@router.get("/api/stats")
async def get_dashboard_stats(
        admin_service: AdminService = Depends(get_admin_service)
) -> dict[str, Any]:
    """API: Получить общую статистику"""
    try:
        return admin_service.get_dashboard_stats()
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/api/analytics")
async def get_sales_analytics(
        days: int = Query(30, ge=1, le=365),
        admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, Any]:
    """API: Получить аналитику продаж"""
    try:
        return admin_service.get_sales_analytics(days=days)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===

@router.get("/api/users")
async def get_users(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        search: Optional[str] = Query(None),
        admin_service: AdminService = Depends(get_admin_service)
) -> List[UserResponse]:
    """API: Получить список пользователей"""
    try:
        users = admin_service.get_all_users(skip=skip, limit=limit, search=search)
        return [UserResponse.model_validate(user) for user in users]
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/users/{user_id}/toggle-status")
async def toggle_user_status(
        user_id: str,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> UserResponse:
    """API: Активировать/деактивировать пользователя"""
    try:
        if user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Нельзя изменить свой статус")

        user = admin_service.toggle_user_status(user_id)
        return UserResponse.model_validate(user)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/users/{user_id}/make-admin")
async def make_user_admin(
        user_id: str,
        admin_service: AdminService = Depends(get_admin_service)
) -> UserResponse:
    """API: Назначить пользователя администратором"""
    try:
        user = admin_service.make_admin(user_id)
        return UserResponse.model_validate(user)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === УПРАВЛЕНИЕ ТОВАРАМИ ===

@router.post("/api/products")
async def create_product(
        product: ProductCreate,
        admin_service: AdminService = Depends(get_admin_service)
) -> ProductResponse:
    """API: Создать новый товар"""
    try:
        created_product = admin_service.create_product(product)
        return ProductResponse.model_validate(created_product)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/products/{product_id}")
async def update_product(
        product_id: str,
        product: ProductUpdate,
        admin_service: AdminService = Depends(get_admin_service)
) -> ProductResponse:
    """API: Обновить товар"""
    try:
        updated_product = admin_service.update_product(product_id, product)
        return ProductResponse.model_validate(updated_product)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/products/{product_id}")
async def delete_product(
        product_id: str,
        admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, str]:
    """API: Удалить товар"""
    try:
        admin_service.delete_product(product_id)
        return {"message": "Товар успешно удален"}
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/api/products/{product_id}/stock")
async def update_product_stock(
        product_id: str,
        stock: int = Form(..., ge=0),
        admin_service: AdminService = Depends(get_admin_service)
) -> ProductResponse:
    """API: Обновить остатки товара"""
    try:
        updated_product = admin_service.update_product_stock(product_id, stock)
        return ProductResponse.model_validate(updated_product)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === УПРАВЛЕНИЕ ЗАКАЗАМИ ===

@router.patch("/api/orders/{order_id}/status")
async def update_order_status(
        order_id: str,
        status: str = Form(...),
        admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, Any]:
    """API: Обновить статус заказа"""
    try:
        allowed_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимый статус. Доступные значения: {', '.join(allowed_statuses)}"
            )

        updated_order = admin_service.update_order_status(order_id, status)
        return {"message": "Статус заказа успешно обновлен", "order": updated_order}
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла внутренняя ошибка сервера {e}")


# === УПРАВЛЕНИЕ ОТЗЫВАМИ ===

@router.get("/api/reviews")
async def get_reviews(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        admin_service: AdminService = Depends(get_admin_service)
) -> list[type[Review]]:
    """API: Получить список отзывов"""
    try:
        return admin_service.get_all_reviews(skip=skip, limit=limit)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/reviews/{review_id}")
async def delete_review(
        review_id: str,
        admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, str]:
    """API: Удалить отзыв"""
    try:
        admin_service.delete_review(review_id)
        return {"message": "Отзыв успешно удален"}
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/orders", response_model=List[OrderResponse])
async def get_orders(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        status: Optional[str] = Query(None),
        admin_service: AdminService = Depends(get_admin_service)
    ):
    """API: Получить список заказов"""
    try:
        return admin_service.get_all_orders(skip=skip, limit=limit, status=status)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))