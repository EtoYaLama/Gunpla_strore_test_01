from app.schemas.history import ViewHistoryBase, ViewHistoryCreate, ViewHistoryResponse, ViewHistoryList, FavoritesBase, FavoritesCreate, FavoritesResponse, FavoritesList
from app.schemas.order import CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse, OrderListResponse, OrderCreate, OrderResponse, OrderUpdate, OrderStatsResponse
from app.schemas.product import ProductBase, ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, ProductFilter, ProductImageUpload
from app.schemas.review import ReviewBase, ReviewCreate, ReviewUpdate, ReviewImageUpload, UserInReview, ProductInReview, Review, ReviewList, ReviewStats, ReviewHelpfulCreate, ReviewHelpful
from app.schemas.user import UserBase, UserCreate, UserLogin, UserUpdate, UserResponse, UserProfile, Token, TokenData

''' Экспортируем все модели для удобного импорта '''
__all__ = [
    'ViewHistoryBase', 'ViewHistoryCreate', 'ViewHistoryResponse', 'ViewHistoryList', 'FavoritesBase', 'FavoritesCreate', 'FavoritesResponse', 'FavoritesList',
    'CartItemCreate', 'CartItemUpdate', 'CartItemResponse', 'CartResponse', 'OrderListResponse', 'OrderCreate', 'OrderResponse', 'OrderUpdate', 'OrderStatsResponse',
    'ProductBase', 'ProductCreate', 'ProductUpdate', 'ProductResponse', 'ProductListResponse', 'ProductFilter', 'ProductImageUpload',
    'ReviewBase', 'ReviewCreate', 'ReviewUpdate', 'ReviewImageUpload', 'UserInReview', 'ProductInReview', 'Review', 'ReviewList', 'ReviewStats', 'ReviewHelpfulCreate', 'ReviewHelpful',
    'UserBase', 'UserCreate', 'UserLogin', 'UserUpdate', 'UserResponse', 'UserProfile', 'Token', 'TokenData'
]