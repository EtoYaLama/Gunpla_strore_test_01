from typing import Dict, Any, List
from pydantic import BaseModel

class AdminStatsResponse(BaseModel):
    users: Dict[str, Any]
    products: Dict[str, Any]
    orders: Dict[str, Any]
    reviews: Dict[str, Any]

class SalesAnalyticsResponse(BaseModel):
    period_days: int
    daily_sales: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    new_users_month: int
    inactive_users: int

class ProductStatsResponse(BaseModel):
    total_products: int
    in_stock: int
    out_of_stock: int
    avg_price: float
    popular_products: List[Dict[str, Any]]

class OrderStatsResponse(BaseModel):
    total_orders: int
    pending_orders: int
    completed_orders: int
    total_revenue: float
    month_revenue: float
    avg_order_value: float

class ReviewStatsResponse(BaseModel):
    total_reviews: int
    avg_rating: float
    month_reviews: int
    rating_1: int
    rating_2: int
    rating_3: int
    rating_4: int
    rating_5: int