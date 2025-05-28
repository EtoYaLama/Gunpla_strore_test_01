from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from sqlalchemy.orm import Session
from typing import Optional
from app.services.auth_service import get_current_user
from app.database import get_db
from app.models import User, Order, OrderItem, Review, Product, ViewHistory

router = APIRouter(prefix='/profile', tags=['profile'])


''' Главная страница личного кабинета '''
@router.get('/', response_class=HTMLResponse)
async def profile_dashboard(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """ Получаем последние заказы """
    recent_orders = db.query(Order).filter(
        and_(
            Order.user_id == current_user.id
        )
    ).order_by(Order.created_at.desc()).limit(5).all()

    ''' Получаем статистику '''
    total_orders = db.query(Order).filter(and_(Order.user_id == current_user.id)).count()
    pending_orders = db.query(Order).filter(
        and_(
            Order.user_id == current_user.id,
            Order.status == 'pending'
        )
    ).count()

    ''' Получаем последние просмотренные товары '''
    recent_views = db.query(ViewHistory).filter(
        and_(
            ViewHistory.user_id == current_user.id
        )
    ).order_by(ViewHistory.viewed_at.desc()).limit(6).all()

    recent_products = []
    for view in recent_views:
        product = db.query(Product).filter(and_(Product.id == view.product_id)).first()
        if product:
            recent_products.append(product)

    return templates.TemplateResponse('profile/dashboard.html', {
        'request': request,
        'user': current_user,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_products': recent_products,
        'active_tab': 'dashboard'
    })


''' История заказов пользователя '''
@router.get('/orders', response_class=HTMLResponse)
async def user_orders(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    per_page = 10
    offset = (page - 1) * per_page

    orders = db.query(Order).filter(
        and_(
            Order.user_id == current_user.id
        )
    ).order_by(Order.created_at.desc()).offset(offset).limit(per_page).all()

    total_orders = db.query(Order).filter(and_(Order.user_id == current_user.id)).count()
    total_pages = (total_orders + per_page - 1) // per_page

    ''' Получаем товары для каждого заказа '''
    for order in orders:
        order.items = db.query(OrderItem).filter(and_(OrderItem.order_id == order.id)).all()
        for item in order.items:
            item.product = db.query(Product).filter(and_(Product.id == item.product_id)).first()

    return templates.TemplateResponse('profile/orders.html', {
        'request': request,
        'user': current_user,
        'orders': orders,
        'current_page': page,
        'total_pages': total_pages,
        'active_tab': 'orders'
    })


''' Детали конкретного заказа '''
@router.get('/order/{order_id}', response_class=HTMLResponse)
async def order_details(
        request: Request,
        order_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    ).first()

    if not order:
        return RedirectResponse(url='/profile/orders', status_code=303)

    ''' Получаем товары заказа '''
    order.items = db.query(OrderItem).filter(and_(OrderItem.order_id == order.id)).all()
    for item in order.items:
        item.product = db.query(Product).filter(and_(Product.id == item.product_id)).first()

    return templates.TemplateResponse('profile/order_detail.html', {
        'request': request,
        'user': current_user,
        'order': order,
        'active_tab': 'orders'
    })


''' Отзывы пользователя '''
@router.get('/reviews', response_class=HTMLResponse)
async def user_reviews(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    per_page = 10
    offset = (page - 1) * per_page

    reviews = db.query(Review).filter(
        and_(
            Review.user_id == current_user.id
        )
    ).order_by(Review.created_at.desc()).offset(offset).limit(per_page).all()

    total_reviews = db.query(Review).filter(and_(Review.user_id == current_user.id)).count()
    total_pages = (total_reviews + per_page - 1) // per_page

    ''' Получаем товары для каждого отзыва '''
    for review in reviews:
        review.product = db.query(Product).filter(and_(Product.id == review.product_id)).first()

    return templates.TemplateResponse('profile/reviews.html', {
        'request': request,
        'user': current_user,
        'reviews': reviews,
        'current_page': page,
        'total_pages': total_pages,
        'active_tab': 'reviews'
    })


''' Избранные товары '''
@router.get('/favorites', response_class=HTMLResponse)
async def user_favorites(
        request: Request,
        page: int = 1,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    per_page = 12
    offset = (page - 1) * per_page

    favorites = db.query(Favorite).filter(
        and_(
            Favorite.user_id == current_user.id
        )
    ).order_by(Favorite.created_at.desc()).offset(offset).limit(per_page).all()

    total_favorites = db.query(Favorite).filter(and_(Favorite.user_id == current_user.id)).count()
    total_pages = (total_favorites + per_page - 1) // per_page

    ''' Получаем товары '''
    products = []
    for favorite in favorites:
        product = db.query(Product).filter(and_(Product.id == favorite.product_id)).first()
        if product:
            products.append(product)

    return templates.TemplateResponse('profile/favorites.html', {
        'request': request,
        'user': current_user,
        'products': products,
        'current_page': page,
        'total_pages': total_pages,
        'active_tab': 'favorites'
    })


''' Настройки профиля '''
@router.get('/settings', response_class=HTMLResponse)
async def profile_settings(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse('profile/settings.html', {
        'request': request,
        'user': current_user,
        'active_tab': 'settings'
    })


''' Обновление профиля пользователя '''
@router.post('/settings')
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
    from ..services.auth_service import verify_password, get_password_hash

    ''' Обновляем основную информацию '''
    current_user.full_name = full_name
    current_user.phone = phone
    current_user.address = address

    ''' Если указан новый пароль '''
    if new_password and current_password:
        if not verify_password(current_password, current_user.password_hash):
            return templates.TemplateResponse('profile/settings.html', {
                'request': request,
                'user': current_user,
                'active_tab': 'settings',
                'error': 'Неверный текущий пароль'
            })

        current_user.password_hash = get_password_hash(new_password)

    db.commit()

    return templates.TemplateResponse('profile/settings.html', {
        'request': request,
        'user': current_user,
        'active_tab': 'settings',
        'success': 'Профиль успешно обновлен'
    })
