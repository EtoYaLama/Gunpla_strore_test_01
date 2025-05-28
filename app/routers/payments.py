from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import hashlib
import hmac
from datetime import datetime

from ..database import get_db
from ..models.order import Order
from ..models.user import User
from ..services.payment_service import PaymentService
from ..utils.dependencies import get_current_user
from ..config import settings

router = APIRouter(prefix="/api/payments", tags=["payments"])
payment_service = PaymentService()


@router.post("/click/prepare")
async def click_prepare(
        request: Request,
        db: Session = Depends(get_db)
):
    """Подготовка платежа через Click"""
    try:
        body = await request.json()

        # Валидация подписи Click
        if not payment_service.verify_click_signature(body):
            raise HTTPException(status_code=400, detail="Invalid signature")

        order_id = body.get("merchant_trans_id")
        amount = body.get("amount")

        # Проверяем заказ
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": -5, "error_note": "Order not found"}

        if order.status != "pending":
            return {"error": -4, "error_note": "Order already processed"}

        if float(order.total_amount) != float(amount) / 100:  # Click передает в тийинах
            return {"error": -2, "error_note": "Incorrect amount"}

        return {
            "click_trans_id": body.get("click_trans_id"),
            "merchant_trans_id": order_id,
            "merchant_prepare_id": f"prep_{order_id}_{datetime.now().timestamp()}",
            "error": 0,
            "error_note": "Success"
        }

    except Exception as e:
        return {"error": -9, "error_note": str(e)}


@router.post("/click/complete")
async def click_complete(
        request: Request,
        db: Session = Depends(get_db)
):
    """Завершение платежа через Click"""
    try:
        body = await request.json()

        # Валидация подписи
        if not payment_service.verify_click_signature(body):
            raise HTTPException(status_code=400, detail="Invalid signature")

        order_id = body.get("merchant_trans_id")

        # Находим заказ
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": -5, "error_note": "Order not found"}

        # Обновляем статус заказа
        order.status = "confirmed"
        order.payment_id = body.get("click_trans_id")
        order.payment_method = "click"
        order.updated_at = datetime.utcnow()

        db.commit()

        return {
            "click_trans_id": body.get("click_trans_id"),
            "merchant_trans_id": order_id,
            "error": 0,
            "error_note": "Success"
        }

    except Exception as e:
        db.rollback()
        return {"error": -9, "error_note": str(e)}


@router.post("/payme/check-perform-transaction")
async def payme_check_perform_transaction(
        request: Request,
        db: Session = Depends(get_db)
):
    """Проверка возможности выполнения транзакции PayMe"""
    try:
        body = await request.json()

        # Валидация авторизации PayMe
        if not payment_service.verify_payme_auth(request.headers.get("Authorization", "")):
            raise HTTPException(status_code=401, detail="Unauthorized")

        params = body.get("params", {})
        account = params.get("account", {})
        order_id = account.get("order_id")
        amount = params.get("amount")

        # Проверяем заказ
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {
                "error": {
                    "code": -31050,
                    "message": "Order not found"
                }
            }

        if order.status != "pending":
            return {
                "error": {
                    "code": -31051,
                    "message": "Order already processed"
                }
            }

        if int(order.total_amount * 100) != amount:  # PayMe работает в тийинах
            return {
                "error": {
                    "code": -31001,
                    "message": "Incorrect amount"
                }
            }

        return {"result": {"allow": True}}

    except Exception as e:
        return {
            "error": {
                "code": -32400,
                "message": str(e)
            }
        }


@router.post("/payme/create-transaction")
async def payme_create_transaction(
        request: Request,
        db: Session = Depends(get_db)
):
    """Создание транзакции PayMe"""
    try:
        body = await request.json()

        if not payment_service.verify_payme_auth(request.headers.get("Authorization", "")):
            raise HTTPException(status_code=401, detail="Unauthorized")

        params = body.get("params", {})
        transaction_id = params.get("id")
        account = params.get("account", {})
        order_id = account.get("order_id")

        # Находим заказ
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {
                "error": {
                    "code": -31050,
                    "message": "Order not found"
                }
            }

        # Обновляем заказ
        order.payment_id = transaction_id
        order.payment_method = "payme"
        order.updated_at = datetime.utcnow()

        db.commit()

        return {
            "result": {
                "create_time": int(datetime.utcnow().timestamp() * 1000),
                "transaction": transaction_id,
                "state": 1
            }
        }

    except Exception as e:
        db.rollback()
        return {
            "error": {
                "code": -32400,
                "message": str(e)
            }
        }


@router.post("/payme/perform-transaction")
async def payme_perform_transaction(
        request: Request,
        db: Session = Depends(get_db)
):
    """Выполнение транзакции PayMe"""
    try:
        body = await request.json()

        if not payment_service.verify_payme_auth(request.headers.get("Authorization", "")):
            raise HTTPException(status_code=401, detail="Unauthorized")

        params = body.get("params", {})
        transaction_id = params.get("id")

        # Находим заказ по payment_id
        order = db.query(Order).filter(Order.payment_id == transaction_id).first()
        if not order:
            return {
                "error": {
                    "code": -31003,
                    "message": "Transaction not found"
                }
            }

        # Подтверждаем заказ
        order.status = "confirmed"
        order.updated_at = datetime.utcnow()

        db.commit()

        return {
            "result": {
                "perform_time": int(datetime.utcnow().timestamp() * 1000),
                "transaction": transaction_id,
                "state": 2
            }
        }

    except Exception as e:
        db.rollback()
        return {
            "error": {
                "code": -32400,
                "message": str(e)
            }
        }


@router.get("/methods")
async def get_payment_methods():
    """Получение доступных методов оплаты"""
    return {
        "methods": [
            {
                "id": "click",
                "name": "Click",
                "description": "Оплата через Click",
                "logo": "/static/images/click-logo.png",
                "enabled": True
            },
            {
                "id": "payme",
                "name": "PayMe",
                "description": "Оплата через PayMe",
                "logo": "/static/images/payme-logo.png",
                "enabled": True
            },
            {
                "id": "uzcard",
                "name": "UzCard",
                "description": "Оплата картой UzCard",
                "logo": "/static/images/uzcard-logo.png",
                "enabled": True
            },
            {
                "id": "visa",
                "name": "Visa/MasterCard",
                "description": "Оплата международными картами",
                "logo": "/static/images/visa-logo.png",
                "enabled": True
            }
        ]
    }


@router.post("/initiate/{method}")
async def initiate_payment(
        method: str,
        order_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Инициация платежа"""
    # Проверяем заказ
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order already processed")

    try:
        # Инициируем платеж через соответствующий сервис
        payment_url = await payment_service.initiate_payment(method, order)

        return {
            "payment_url": payment_url,
            "order_id": order_id,
            "amount": float(order.total_amount),
            "method": method
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))