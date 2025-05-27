from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import uuid


''' Модель пользователя (Базовая) '''
class UserBase(BaseModel):
    email: EmailStr = Field(..., description='Почта пользователя')
    username: str = Field(..., description='UserName пользователя')
    full_name: Optional[str] = Field(None, description='Имя пользователя')


''' Модель пользователя (Расширенный) '''
class UserCreate(UserBase):
    password: str = Field(..., description='Пароль пользователя')

    ''' Валидация пароля '''
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v

    ''' Валидация имени пользователя '''
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Имя пользователя должно содержать минимум 3 символа')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Имя пользователя может содержать только буквы, цифры, _ и -')
        return v

''' Метод для авторизации пользователя в системе '''
class UserLogin(BaseModel):
    email: EmailStr
    password: str


''' Метод для обновления данных текущего пользователя '''
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description='Имя пользователя')
    phone: Optional[str] = Field(None, description='Телефонный номер пользователя')
    address: Optional[str] = Field(None, description='Адрес доставки пользователя')


''' Метод для ответа '''
class UserResponse(UserBase):
    id: uuid.UUID = Field(..., description='ID')
    phone: Optional[str] = Field(None, description='Телефонный номер')
    address: Optional[str] = Field(None, description='Адрес доставки пользователя')
    is_admin: bool = Field(..., description='Является ли пользователь администратором')
    is_active: bool = Field(..., description='Активен ли пользователь')
    created_at: datetime = Field(..., description='Дата создания пользователя')

    ''' Поддержка маппинга SQLAlchemy объектов '''
    class Config:
        from_attributes = True


''' Модель профиля пользователя '''
class UserProfile(UserResponse):
    pass


''' Схемы для токенов '''
class Token(BaseModel):
    access_token: str = Field(..., description='Токен доступа')
    token_type: str = Field(..., description='Тип токена (Обычный, Bearer)')


''' Вспомогательная схема для работы с токенами '''
class TokenData(BaseModel):
    email: Optional[str] = Field(None, description='Почта, связанная с токеном')