import hashlib
import hmac
import base64
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from ..config import settings
from ..models.order import Order


class PaymentService:
    def __init__(self):
        self.click_service_id = settings.CLICK_SERVICE_ID
        self.click_secret_key = settings.CLICK_SECRET_KEY
        self.payme_merchant_id = settings.PAYME_MERCHANT_ID
        self.payme_secret_key = settings.PAYME_SECRET_KEY

    def verify_click_signature(self, data: Dict[str, Any]) -> bool:
        """Проверка подписи Click"""
        try:
            # Параметры для подписи в определенном порядке
            sign_string = (
                f"{data.get('click_trans_id', '')}"
                f"{data.get('service_id', '')}"
                f"{self.click_secret_key}"
                f"{data.get('merchant_trans_id', '')}"
                f"{data.get('amount', '')}"
                f"{data.get('action', '')}"
                f"{data.get('sign_time', '')}"
            )

            # Создаем подпись
            expected_signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
            received_signature = data.get('sign_string', '')

            return expected_signature == received_signature

        except Exception:
            return False

    def verify_payme_auth(self, authorization: str) -> bool:
        """Проверка авторизации PayMe"""
        try:
            if not authorization.startswith('Basic '):
                return False

            # Декодируем Base64
            encoded_credentials = authorization[6:]  # Убираем 'Basic '
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')

            # Формат: Payme:{merchant_id}
            expected_auth = f"Payme:{self.payme_secret_key}"

            return decoded_credentials == expected_auth

        except Exception:
            return False

    async def initiate_payment(self, method: str, order: Order) -> str:
        """Инициация платежа в зависимости от метода"""
        if method == "click":
            return await self._initiate_click_payment(order)
        elif method == "payme":
            return await self._initiate_payme_payment(order)
        elif method == "uzcard":
            return await self._initiate_uzcard_payment(order)
        elif method == "visa":
            return await self._initiate_visa_payment(order)
        else:
            raise ValueError(f"Unsupported payment method: {method}")

    async def _initiate_click_payment(self, order: Order) -> str:
        """Инициация платежа через Click"""
        # Click обычно использует прямые ссылки для оплаты
        params = {
            'service_id': self.click_service_id,
            'merchant_id': order.id,
            'amount': int(order.total_amount * 100),  # В тийинах
            'transaction_param': order.id,
            'return_url': f"{settings.BASE_URL}/payment/success",
            'cancel_url': f"{settings.BASE_URL}/payment/cancel"
        }

        # Создаем URL для оплаты
        click_url = "https://my.click.uz/services/pay"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return f"{click_url}?{query_string}"

    async def _initiate_payme_payment(self, order: Order) -> str:
        """Инициация платежа через PayMe"""
        # PayMe использует encoded данные в URL
        account = {
            'order_id': str(order.id)
        }

        # Кодируем данные в base64
        encoded_account = base64.b64encode(
            json.dumps(account).encode('utf-8')
        ).decode('utf-8')

        payme_url = (
            f"https://checkout.paycom.uz/{base64.b64encode(self.payme_merchant_id.encode()).decode()}"
            f"?ac.order_id={order.id}"
            f"&a={int(order.total_amount * 100)}"  # В тийинах
            f"&c={encoded_account}"
        )

        return payme_url

    async def _initiate_uzcard_payment(self, order: Order) -> str:
        """Инициация платежа через UzCard"""
        # Пример интеграции с UzCard (требует документацию от провайдера)
        try:
            uzcard_api_url = "https://api.uzcard.uz/api/v1/payment/create"

            payload = {
                'merchant_id': settings.UZCARD_MERCHANT_ID,
                'order_id': str(order.id),
                'amount': int(order.total_amount * 100),
                'currency': 'UZS',
                'description': f'Заказ #{order.id}',
                'return_url': f"{settings.BASE_URL}/payment/success",
                'cancel_url': f"{settings.BASE_URL}/payment/cancel"
            }

            # Создаем подпись для UzCard
            signature = self._create_uzcard_signature(payload)
            payload['signature'] = signature

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {settings.UZCARD_API_KEY}'
            }

            response = requests.post(uzcard_api_url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            return result.get('payment_url', '')

        except Exception as e:
            raise ValueError(f"UzCard payment initiation failed: {str(e)}")

    async def _initiate_visa_payment(self, order: Order) -> str:
        """Инициация платежа через Visa/MasterCard"""
        # Пример интеграции с процессинговым центром
        try:
            visa_api_url = "https://api.processing.uz/api/v1/payment/create"

            payload = {
                'merchant_id': settings.VISA_MERCHANT_ID,
                'order_id': str(order.id),
                'amount': int(order.total_amount * 100),
                'currency': 'UZS',
                'description': f'GUNPLA заказ #{order.id}',
                'return_url': f"{settings.BASE_URL}/payment/success",
                'cancel_url': f"{settings.BASE_URL}/payment/cancel",
                'card_types': ['visa', 'mastercard']
            }

            # Создаем подпись
            signature = self._create_visa_signature(payload)
            payload['signature'] = signature

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {settings.VISA_API_KEY}'
            }

            response = requests.post(visa_api_url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            return result.get('payment_url', '')

        except Exception as e:
            raise ValueError(f"Visa payment initiation failed: {str(e)}")

    def _create_uzcard_signature(self, payload: Dict[str, Any]) -> str:
        """Создание подписи для UzCard"""
        # Сортируем параметры и создаем строку для подписи
        sorted_params = sorted(payload.items())
        sign_string = ''.join([f"{k}={v}" for k, v in sorted_params if k != 'signature'])
        sign_string += settings.UZCARD_SECRET_KEY

        return hashlib.sha256(sign_string.encode('utf-8')).hexdigest()

    def _create_visa_signature(self, payload: Dict[str, Any]) -> str:
        """Создание подписи для Visa/MasterCard"""
        # Создаем строку для подписи
        sign_string = (
            f"{payload['merchant_id']}"
            f"{payload['order_id']}"
            f"{payload['amount']}"
            f"{payload['currency']}"
            f"{settings.VISA_SECRET_KEY}"
        )

        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    async def verify_payment_status(self, method: str, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа"""
        if method == "click":
            return await self._verify_click_status(payment_id)
        elif method == "payme":
            return await self._verify_payme_status(payment_id)
        elif method == "uzcard":
            return await self._verify_uzcard_status(payment_id)
        elif method == "visa":
            return await self._verify_visa_status(payment_id)
        else:
            return {"status": "unknown", "message": "Unsupported payment method"}

    async def _verify_click_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа Click"""
        # Обычно Click присылает callback, но можно проверить статус
        return {"status": "pending", "message": "Click status check not implemented"}

    async def _verify_payme_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа PayMe"""
        try:
            payme_api_url = "https://checkout.paycom.uz/api"

            payload = {
                "method": "GetStatement",
                "params": {
                    "from": int((datetime.now().timestamp() - 86400) * 1000),  # 24 часа назад
                    "to": int(datetime.now().timestamp() * 1000)
                }
            }

            auth_string = base64.b64encode(f"Payme:{self.payme_secret_key}".encode()).decode()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth_string}'
            }

            response = requests.post(payme_api_url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            # Ищем нашу транзакцию
            for transaction in result.get('result', {}).get('transactions', []):
                if transaction.get('id') == payment_id:
                    state = transaction.get('state')
                    if state == 2:
                        return {"status": "completed", "message": "Payment successful"}
                    elif state == -1 or state == -2:
                        return {"status": "cancelled", "message": "Payment cancelled"}
                    else:
                        return {"status": "pending", "message": "Payment in progress"}

            return {"status": "not_found", "message": "Transaction not found"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _verify_uzcard_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа UzCard"""
        # Реализация зависит от API UzCard
        return {"status": "pending", "message": "UzCard status check not implemented"}

    async def _verify_visa_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа Visa"""
        # Реализация зависит от процессингового центра
        return {"status": "pending", "message": "Visa status check not implemented"}

    def format_amount(self, amount: float, currency: str = "UZS") -> str:
        """Форматирование суммы для отображения"""
        if currency == "UZS":
            return f"{amount:,.0f} сум"
        elif currency == "USD":
            return f"${amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"