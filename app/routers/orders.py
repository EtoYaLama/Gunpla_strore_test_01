from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

from ..database import get_db
from ..models.user import User
from ..models.product import Product
from ..models.order import Cart, Order, OrderItem, OrderStatus
from ..schemas.order import (
    CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse,
    OrderCreate, OrderResponse, OrderUpdate, OrderListResponse, OrderStatsResponse
)
from ..utils.dependencies import get_current_user, get_current_admin_user
from ..services.file_service import file_service

router = APIRouter(prefix="/orders", tags=["orders"])


# ==================== КОРЗИНА ====================

@router.get("/cart", response_model=CartResponse)
async def get_cart(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение корзины пользователя"""

    # Получаем элементы корзины с информацией о товарах
    cart_items = db.query(Cart, Product).join(
        Product, Cart.product_id == Product.id
    ).filter(Cart.user_id == current_user.id).all()

    items_response = []
    total_amount = Decimal('0')

    for cart_item, product in cart_items:
        # Проверяем доступность товара
        available_quantity = min(cart_item.quantity, product.in_stock)
        item_total = product.price * available_quantity
        total_amount += item_total

        items_response.append(CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            created_at=cart_item.created_at,
            product_name=product.name,
            product_price=product.price,
            product_image=file_service.get_image_url(product.main_image, "thumbnail"),
            product_in_stock=product.in_stock,
            total_price=item_total
        ))

    return CartResponse(
        items=items_response,
        total_items=len(items_response),
        total_amount=total_amount
    )


@router.post("/cart/add")
async def add_to_cart(
        item: CartItemCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Добавление товара в корзину"""

    # Проверяем существование товара
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Проверяем наличие
    if product.in_stock < item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"В наличии только {product.in_stock} шт."
        )

    # Проверяем, есть ли уже этот товар в корзине
    existing_item = db.query(Cart).filter(
        and_(Cart.user_id == current_user.id, Cart.product_id == item.product_id)
    ).first()

    if existing_item:
        # Обновляем количество
        new_quantity = existing_item.quantity + item.quantity
        if new_quantity > product.in_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Общее количество превышает доступное ({product.in_stock} шт.)"
            )
        existing_item.quantity = new_quantity
    else:
        # Создаем новый элемент корзины
        cart_item = Cart(
            user_id=current_user.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(cart_item)

    db.commit()
    return {"message": "Товар добавлен в корзину"}


@router.put("/cart/{item_id}")
async def update_cart_item(
        item_id: str,
        item: CartItemUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновление количества товара в корзине"""

    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID")