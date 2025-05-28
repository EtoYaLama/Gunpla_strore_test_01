from app.schemas.history import ViewHistoryBase, ViewHistoryCreate, ViewHistoryResponse, ViewHistoryList, FavoritesBase, FavoritesCreate, FavoritesResponse, FavoritesList, FavoritesToggleResponse
from app.schemas.order import CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse, OrderListResponse, OrderCreate, OrderResponse, OrderUpdate, OrderStatsResponse
from app.schemas.product import ProductBase, ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, ProductFilter, ProductImageUpload
from app.schemas.review import ReviewBase, ReviewCreate, ReviewUpdate, ReviewImageUpload, UserInReview, ProductInReview, Review, ReviewList, ReviewStats, ReviewHelpfulCreate, ReviewHelpful
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserLogin, UserProfile, Token, TokenData
from app.schemas.payments import PaymentMethod, PaymentStatus, PaymentCreate, PaymentResponse, PaymentCallback, ClickPrepareRequest, ClickCompleteRequest, ClickResponse, PayMeRequest, PayMeResponse
from app.schemas.admin import AdminStatsResponse, SalesAnalyticsResponse, UserStatsResponse, ProductStatsResponse, OrderStatsResponse, ReviewStatsResponse


''' Экспортируем все модели для удобного импорта '''
__all__ = [
    'ViewHistoryBase', 'ViewHistoryCreate', 'ViewHistoryResponse', 'ViewHistoryList', 'FavoritesBase', 'FavoritesCreate', 'FavoritesResponse', 'FavoritesList', 'FavoritesToggleResponse',
    'CartItemCreate', 'CartItemUpdate', 'CartItemResponse', 'CartResponse', 'OrderListResponse', 'OrderCreate', 'OrderResponse', 'OrderUpdate', 'OrderStatsResponse',
    'ProductBase', 'ProductCreate', 'ProductUpdate', 'ProductResponse', 'ProductListResponse', 'ProductFilter', 'ProductImageUpload',
    'ReviewBase', 'ReviewCreate', 'ReviewUpdate', 'ReviewImageUpload', 'UserInReview', 'ProductInReview', 'Review', 'ReviewList', 'ReviewStats', 'ReviewHelpfulCreate', 'ReviewHelpful',
    'UserBase', 'UserCreate', 'UserUpdate', 'UserResponse', 'UserLogin', 'UserProfile', 'Token', 'TokenData',
    'PaymentMethod', 'PaymentStatus', 'PaymentCreate', 'PaymentResponse', 'PaymentCallback', 'ClickPrepareRequest', 'ClickCompleteRequest', 'ClickResponse', 'PayMeRequest', 'PayMeResponse',
    'AdminStatsResponse', 'SalesAnalyticsResponse', 'UserStatsResponse', 'ProductStatsResponse', 'OrderStatsResponse', 'ReviewStatsResponse'

]