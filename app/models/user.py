from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.models import BaseModel


''' Таблица пользователя '''
class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False) # Почта пользователя
    username = Column(String(50), unique=True, index=True, nullable=False) # UserName пользователя
    password_hash = Column(String(255), nullable=False) # Хэшированный пароль пользователя
    full_name = Column(String(100), nullable=True) # Полное имя пользователя
    phone = Column(String(20), nullable=True) # Телефонный номер пользователя
    address = Column(Text, nullable=True) # Адрес пользователя
    is_admin = Column(Boolean, default=False, nullable=False) # Статус Admin
    is_active = Column(Boolean, default=True, nullable=False) # Статус Пользователь

    ''' Создаем связь между таблицами Order, Cart, Review, ViewHistory, Favorite '''
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    view_history = relationship("ViewHistory", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")


    ''' Пример отображения объекта '''
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


    ''' Отображение имени пользователя '''
    @property
    def display_name(self):
        return self.full_name or self.username