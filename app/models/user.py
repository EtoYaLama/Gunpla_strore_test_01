from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Связи с другими таблицами
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    view_history = relationship("ViewHistory", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"