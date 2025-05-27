from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid
from app.models import OrderStatusEnum

'''  Модель добавления нового товара в корзину пользователя '''
class CartItemCreate(BaseModel):
    product_id: uuid.UUID = Field(..., description='ID товара, который добавляется в корзину')
    quantity: int = Field(..., ge=1, description='Количество товара, добавляемого в корзину')


''' Модель для обновления количества товара в корзине '''
class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description='Новое количество товара в корзине')


''' Модель для ответа, описывающая один элемент корзины '''
class CartItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int = Field(..., ge=1, description='Количество товара в корзине')
    created_at: datetime = Field(..., description='Дата и время добавления товара в корзину')
    product_name: str = Field(..., description='Название товара')
    product_price: Decimal = Field(..., description='Цена товара')
    product_image: Optional[str] = Field(None, description='Уменьшенное изображение товара')
    product_in_stock: int = Field(..., ge=0, description='Количество товара на складе')
    total_price: Decimal = Field(..., description='Общая стоимость для данного товара (цена x количество)')


''' Модель для ответа с информацией о корзине '''
class CartResponse(BaseModel):
    items: List[CartItemResponse] = Field(..., description='Список элементов корзины')
    total_items: int = Field(..., ge=0, description='Общее количество уникальных товаров в корзине')
    total_amount: Decimal = Field(..., ge=0, description='Общая стоимость всех товаров в корзине')


''' Модель для отображения списка заказов '''
class OrderListResponse(BaseModel):
    id: uuid.UUID = Field(..., description='Уникальный ID заказа')
    status: OrderStatusEnum = Field(..., description='Текущий статус заказа')
    created_at: datetime = Field(..., description='Дата и время создания заказа')
    total_amount: Decimal = Field(..., description='Итоговая сумма заказа')
    shipping_address: Optional[str] = Field(None, description='Адрес доставки')
    items_count: int = Field(..., ge=0, description='Количество уникальных товаров в заказе')


''' Модель для создания заказа '''
class OrderCreate(BaseModel):
    cart_items: List[uuid.UUID] = Field(..., description='Список ID товаров из корзины для заказа')
    shipping_address: str = Field(..., min_length=5, description='Адрес доставки')
    total_amount: Decimal = Field(..., gt=0, description='Итоговая сумма заказа')


''' Модель для ответа о заказе '''
class OrderResponse(BaseModel):
    id: uuid.UUID = Field(..., description='Уникальный ID заказа')
    status: OrderStatusEnum = Field(..., description='Текущий статус заказа')
    created_at: datetime = Field(..., description='Дата и время создания заказа')
    cart: CartResponse = Field(..., description='Сведения о товарах, включённых в заказ')
    total_amount: Decimal = Field(..., description='Итоговая сумма заказа')
    shipping_address: str = Field(..., description='Адрес доставки заказа')


''' Модель для обновления заказа '''
class OrderUpdate(BaseModel):
    status: OrderStatusEnum = Field(..., description='Новый статус заказа')


''' Модель для статистики заказов '''
class OrderStatsResponse(BaseModel):
    total_orders: int = Field(..., ge=0, description='Общее количество заказов')
    successful_orders: int = Field(..., ge=0, description='Количество успешно выполненных заказов')
    total_revenue: Decimal = Field(..., ge=0, description='Общий доход от заказов')
    orders_last_30_days: int = Field(..., ge=0, description='Количество заказов за последние 30 дней')
