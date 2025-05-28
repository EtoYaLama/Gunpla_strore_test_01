from pydantic import BaseModel
from typing import Optional, Dict, Any
from decimal import Decimal
from enum import Enum

class PaymentMethod(str, Enum):
    CLICK = "click"
    PAYME = "payme"
    UZCARD = "uzcard"
    VISA = "visa"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentCreate(BaseModel):
    order_id: str
    amount: Decimal
    method: PaymentMethod
    return_url: Optional[str] = None

class PaymentResponse(BaseModel):
    payment_id: str
    payment_url: Optional[str] = None
    status: PaymentStatus
    message: str

class PaymentCallback(BaseModel):
    payment_id: str
    status: str
    amount: Optional[Decimal] = None
    transaction_id: Optional[str] = None
    signature: Optional[str] = None
    # Дополнительные поля для разных платежных систем
    extra_data: Optional[Dict[str, Any]] = None

# Click специфичные схемы
class ClickPrepareRequest(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    amount: float
    action: int
    error: int
    error_note: str
    sign_time: str
    sign_string: str

class ClickCompleteRequest(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    amount: float
    action: int
    error: int
    error_note: str
    sign_time: str
    sign_string: str

class ClickResponse(BaseModel):
    click_trans_id: int
    merchant_trans_id: str
    merchant_prepare_id: Optional[int] = None
    error: int
    error_note: str

# PayMe специфичные схемы
class PayMeRequest(BaseModel):
    method: str
    params: Dict[str, Any]

class PayMeResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: int