# app/routers/profile.py
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from ..database import get_db
from ..models.user import User
from ..models.order import Order, OrderItem
from ..models.review import Review
from ..models.product import Product
from ..models.history import ViewHistory
from ..models.favorite import Favorite
from ..services.auth_service import get_current_user
from ..services.file_service import save_uploaded_file
from ..utils.dependencies import templates

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_class=HTMLResponse)
async def profile_dashboard(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Главная страница личного кабинета"""

    # Получаем последние заказы
    recent_orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()

    # Получаем статистику
    total_orders = db.query(Order).filter(Order.user_id == current_user.id).count()
    pending_orders = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.status == "pending"
    ).count()

    # Получаем последние просмотренные товары
    recent_views = db.query(ViewHistory).filter(
        ViewHistory.user_id == current_user.id
    ).order_by(ViewHistory.viewed_at.desc()).limit(6).all()

    recent_products = []
    for view in recent_views:
        product = db.query(Product).filter(Product.id == view.product_id).first()
        if product:
            recent_products.append(product)

    return templates.TemplateResponse("profile/dashboard.html", {
        "request": request,
        "user": current_user,
        "recent_orders": recent_orders,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "recent_products": recent_products,
        "active_tab": "dashboard"
    })


@router.get("/orders", response_class=HTMLResponse)
async def user_orders(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """История заказов пользователя"""

    per_page = 10
    offset = (page - 1) * per_page

    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).offset(offset).limit(per_page).all()

    total_orders = db.query(Order).filter(Order.user_id == current_user.id).count()
    total_pages = (total_orders + per_page - 1) // per_page

    # Получаем товары для каждого заказа
    for order in orders:
        order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in order.items:
            item.product = db.query(Product).filter(Product.id == item.product_id).first()

    return templates.TemplateResponse("profile/orders.html", {
        "request": request,
        "user": current_user,
        "orders": orders,
        "current_page": page,
        "total_pages": total_pages,
        "active_tab": "orders"
    })


@router.get("/order/{order_id}", response_class=HTMLResponse)
async def order_details(
        request: Request,
        order_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Детали конкретного заказа"""

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        return RedirectResponse(url="/profile/orders", status_code=303)

    # Получаем товары заказа
    order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in order.items:
        item.product = db.query(Product).filter(Product.id == item.product_id).first()

    return templates.TemplateResponse("profile/order_detail.html", {
        "request": request,
        "user": current_user,
        "order": order,
        "active_tab": "orders"
    })


@router.get("/reviews", response_class=HTMLResponse)
async def user_reviews(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отзывы пользователя"""

    per_page = 10
    offset = (page - 1) * per_page

    reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).offset(offset).limit(per_page).all()

    total_reviews = db.query(Review).filter(Review.user_id == current_user.id).count()
    total_pages = (total_reviews + per_page - 1) // per_page

    # Получаем товары для каждого отзыва
    for review in reviews:
        review.product = db.query(Product).filter(Product.id == review.product_id).first()

    return templates.TemplateResponse("profile/reviews.html", {
        "request": request,
        "user": current_user,
        "reviews": reviews,
        "current_page": page,
        "total_pages": total_pages,
        "active_tab": "reviews"
    })


@router.get("/favorites", response_class=HTMLResponse)
async def user_favorites(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Избранные товары"""

    per_page = 12
    offset = (page - 1) * per_page

    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(Favorite.created_at.desc()).offset(offset).limit(per_page).all()

    total_favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).count()
    total_pages = (total_favorites + per_page - 1) // per_page

    # Получаем товары
    products = []
    for favorite in favorites:
        product = db.query(Product).filter(Product.id == favorite.product_id).first()
        if product:
            products.append(product)

    return templates.TemplateResponse("profile/favorites.html", {
        "request": request,
        "user": current_user,
        "products": products,
        "current_page": page,
        "total_pages": total_pages,
        "active_tab": "favorites"
    })


@router.get("/settings", response_class=HTMLResponse)
async def profile_settings(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """Настройки профиля"""

    return templates.TemplateResponse("profile/settings.html", {
        "request": request,
        "user": current_user,
        "active_tab": "settings"
    })


@router.post("/settings")
async def update_profile(
        request: Request,
        full_name: str = Form(...),
        phone: str = Form(...),
        address: str = Form(...),
        current_password: Optional[str] = Form(None),
        new_password: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновление профиля пользователя"""

    from ..services.auth_service import verify_password, get_password_hash

    # Обновляем основную информацию
    current_user.full_name = full_name
    current_user.phone = phone
    current_user.address = address

    # Если указан новый пароль
    if new_password and current_password:
        if not verify_password(current_password, current_user.password_hash):
            return templates.TemplateResponse("profile/settings.html", {
                "request": request,
                "user": current_user,
                "active_tab": "settings",
                "error": "Неверный текущий пароль"
            })

        current_user.password_hash = get_password_hash(new_password)

    db.commit()

    return templates.TemplateResponse("profile/settings.html", {
        "request": request,
        "user": current_user,
        "active_tab": "settings",
        "success": "Профиль успешно обновлен"
    })


@router.post("/favorite/toggle")
async def toggle_favorite(
        request: Request,
        product_id: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Добавить/удалить товар из избранного"""

    existing_favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.product_id == product_id
    ).first()

    if existing_favorite:
        db.delete(existing_favorite)
        action = "removed"
    else:
        favorite = Favorite(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            product_id=product_id
        )
        db.add(favorite)
        action = "added"

    db.commit()

    return {"status": "success", "action": action}


@router.get("/history", response_class=HTMLResponse)
async def view_history(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """История просмотров"""

    per_page = 12
    offset = (page - 1) * per_page

    history = db.query(ViewHistory).filter(
        ViewHistory.user_id == current_user.id
    ).order_by(ViewHistory.viewed_at.desc()).offset(offset).limit(per_page).all()

    total_history = db.query(ViewHistory).filter(ViewHistory.user_id == current_user.id).count()
    total_pages = (total_history + per_page - 1) // per_page

    # Получаем товары
    products = []
    for view in history:
        product = db.query(Product).filter(Product.id == view.product_id).first()
        if product:
            product.viewed_at = view.viewed_at
            products.append(product)

    return templates.TemplateResponse("profile/history.html", {
        "request": request,
        "user": current_user,
        "products": products,
        "current_page": page,
        "total_pages": total_pages,
        "active_tab": "history"
    })


@router.post("/history/clear")
async def clear_history(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Очистить историю просмотров"""

    db.query(ViewHistory).filter(ViewHistory.user_id == current_user.id).delete()
    db.commit()

    return RedirectResponse(url="/profile/history", status_code=303)