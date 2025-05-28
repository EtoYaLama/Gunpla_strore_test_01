from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.admin_service import AdminService
from ..services.auth_service import get_current_admin_user
from ..models.user import User
from ..models.product import Product
from ..models.order import Order
from ..models.review import Review
from ..schemas.user import UserResponse, UserUpdate
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse
from ..utils.exceptions import AdminServiceException

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


# === MIDDLEWARE ===

def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """Получить экземпляр AdminService"""
    return AdminService(db)


# === HTML СТРАНИЦЫ ===

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
        request: Request,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Главная страница админ панели"""
    try:
        stats = admin_service.get_dashboard_stats()
        analytics = admin_service.get_sales_analytics(days=30)

        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "user": current_user,
            "stats": stats,
            "analytics": analytics,
            "page_title": "Панель администратора"
        })
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
        request: Request,
        page: int = Query(1, ge=1),
        search: Optional[str] = Query(None),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Страница управления пользователями"""
    try:
        limit = 20
        skip = (page - 1) * limit

        users = admin_service.get_all_users(skip=skip, limit=limit, search=search)
        users_stats = admin_service.get_users_stats()

        return templates.TemplateResponse("admin/users.html", {
            "request": request,
            "user": current_user,
            "users": users,
            "users_stats": users_stats,
            "page": page,
            "search": search or "",
            "page_title": "Управление пользователями"
        })
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products", response_class=HTMLResponse)
async def admin_products_page(
        request: Request,
        page: int = Query(1, ge=1),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service),
        db: Session = Depends(get_db)
):
    """Страница управления товарами"""
    try:
        limit = 20
        skip = (page - 1) * limit

        products = db.query(Product).offset(skip).limit(limit).all()
        products_stats = admin_service.get_products_stats()

        return templates.TemplateResponse("admin/products.html", {
            "request": request,
            "user": current_user,
            "products": products,
            "products_stats": products_stats,
            "page": page,
            "page_title": "Управление товарами"
        })
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", response_class=HTMLResponse)
async def admin_orders_page(
        request: Request,
        page: int = Query(1, ge=1),
        status: Optional[str] = Query(None),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Страница управления заказами"""
    try:
        limit = 20
        skip = (page - 1) * limit

        orders = admin_service.get_all_orders(skip=skip, limit=limit, status=status)
        orders_stats = admin_service.get_orders_stats()

        return templates.TemplateResponse("admin/orders.html", {
            "request": request,
            "user": current_user,
            "orders": orders,
            "orders_stats": orders_stats,
            "page": page,
            "status_filter": status or "",
            "page_title": "Управление заказами"
        })
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reviews", response_class=HTMLResponse)
async def admin_reviews_page(
        request: Request,
        page: int = Query(1, ge=1),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Страница управления отзывами"""
    try:
        limit = 20
        skip = (page - 1) * limit

        reviews = admin_service.get_all_reviews(skip=skip, limit=limit)
        reviews_stats = admin_service.get_reviews_stats()

        return templates.TemplateResponse("admin/reviews.html", {
            "request": request,
            "user": current_user,
            "reviews": reviews,
            "reviews_stats": reviews_stats,
            "page": page,
            "page_title": "Управление отзывами"
        })
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === API ENDPOINTS ===

# === СТАТИСТИКА ===

@router.get("/api/stats")
async def get_dashboard_stats(
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, Any]:
    """API: Получить общую статистику"""
    try:
        return admin_service.get_dashboard_stats()
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/analytics")
async def get_sales_analytics(
        days: int = Query(30, ge=1, le=365),
        current_user: User = Depends(get_current_admin_user),
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
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> List[UserResponse]:
    """API: Получить список пользователей"""
    try:
        users = admin_service.get_all_users(skip=skip, limit=limit, search=search)
        return [UserResponse.from_orm(user) for user in users]
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
        return UserResponse.from_orm(user)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/users/{user_id}/make-admin")
async def make_user_admin(
        user_id: str,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> UserResponse:
    """API: Назначить пользователя администратором"""
    try:
        user = admin_service.make_admin(user_id)
        return UserResponse.from_orm(user)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === УПРАВЛЕНИЕ ТОВАРАМИ ===

@router.post("/api/products")
async def create_product(
        product: ProductCreate,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> ProductResponse:
    """API: Создать новый товар"""
    try:
        created_product = admin_service.create_product(product)
        return ProductResponse.from_orm(created_product)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/products/{product_id}")
async def update_product(
        product_id: str,
        product: ProductUpdate,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> ProductResponse:
    """API: Обновить товар"""
    try:
        updated_product = admin_service.update_product(product_id, product)
        return ProductResponse.from_orm(updated_product)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/products/{product_id}")
async def delete_product(
        product_id: str,
        current_user: User = Depends(get_current_admin_user),
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
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> ProductResponse:
    """API: Обновить остатки товара"""
    try:
        updated_product = admin_service.update_product_stock(product_id, stock)
        return ProductResponse.from_orm(updated_product)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === УПРАВЛЕНИЕ ЗАКАЗАМИ ===

@router.get("/api/orders")
async def get_orders(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        status: Optional[str] = Query(None),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> List[Order]:
    """API: Получить список заказов"""
    try:
        return admin_service.get_all_orders(skip=skip, limit=limit, status=status)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/api/orders/{order_id}/status")
async def update_order_status(
        order_id: str,
        status: str = Form(...),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Order:
    """API: Обновить статус заказа"""
    try:
        allowed_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимый статус. Доступные: {', '.join(allowed_statuses)}"
            )

        updated_order = admin_service.update_order_status(order_id, status)
        return updated_order
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === УПРАВЛЕНИЕ ОТЗЫВАМИ ===

@router.get("/api/reviews")
async def get_reviews(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> List[Review]:
    """API: Получить список отзывов"""
    try:
        return admin_service.get_all_reviews(skip=skip, limit=limit)
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/reviews/{review_id}")
async def delete_review(
        review_id: str,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, str]:
    """API: Удалить отзыв"""
    try:
        admin_service.delete_review(review_id)
        return {"message": "Отзыв успешно удален"}
    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# === ФОРМ-ОБРАБОТЧИКИ ===

@router.post("/users/{user_id}/toggle-status", response_class=HTMLResponse)
async def toggle_user_status_form(
        request: Request,
        user_id: str,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Форма: Изменить статус пользователя"""
    try:
        if user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Нельзя изменить свой статус")

        admin_service.toggle_user_status(user_id)

        # Редирект обратно на страницу пользователей
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin/users", status_code=303)

    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/make-admin", response_class=HTMLResponse)
async def make_admin_form(
        request: Request,
        user_id: str,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Форма: Назначить администратора"""
    try:
        admin_service.make_admin(user_id)

        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin/users", status_code=303)

    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/update-status", response_class=HTMLResponse)
async def update_order_status_form(
        request: Request,
        order_id: str,
        status: str = Form(...),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Форма: Обновить статус заказа"""
    try:
        admin_service.update_order_status(order_id, status)

        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin/orders", status_code=303)

    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/products/{product_id}/update-stock", response_class=HTMLResponse)
async def update_stock_form(
        request: Request,
        product_id: str,
        stock: int = Form(..., ge=0),
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Форма: Обновить остатки товара"""
    try:
        admin_service.update_product_stock(product_id, stock)

        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin/products", status_code=303)

    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reviews/{review_id}/delete", response_class=HTMLResponse)
async def delete_review_form(
        request: Request,
        review_id: str,
        current_user: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
):
    """Форма: Удалить отзыв"""
    try:
        admin_service.delete_review(review_id)

        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin/reviews", status_code=303)

    except AdminServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))