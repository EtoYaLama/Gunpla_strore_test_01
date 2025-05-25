from sqlalchemy import Column, String, Text, DECIMAL, Integer, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class GradeEnum(enum.Enum):
    HG = "HG"  # High Grade 1/144
    RG = "RG"  # Real Grade 1/144
    MG = "MG"  # Master Grade 1/100
    MR_VER_KA = "MR_VER_KA"  # Ver.Ka
    MGEX = "MGEX"  # Master Grade Extreme
    PG = "PG"  # Perfect Grade 1/60


class Product(BaseModel):
    __tablename__ = "products"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    grade = Column(Enum(GradeEnum), nullable=False, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)  # Bandai, Kotobukiya
    series = Column(String(100), nullable=True, index=True)  # Mobile Suit Gundam, Evangelion
    scale = Column(String(20), nullable=True)  # 1/144, 1/100, 1/60
    difficulty = Column(Integer, nullable=True)  # 1-5 звезд сложности
    in_stock = Column(Integer, default=0, nullable=False)

    # Изображения
    main_image = Column(String(255), nullable=True)
    additional_images = Column(JSON, nullable=True)  # Массив путей к доп. фото

    # Рейтинг (вычисляемые поля)
    average_rating = Column(DECIMAL(3, 2), default=0.0)
    total_reviews = Column(Integer, default=0)

    # Связи
    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("Cart", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    view_history = relationship("ViewHistory", back_populates="product")
    favorites = relationship("Favorite", back_populates="product")

    def __repr__(self):
        return f"<Product(name='{self.name}', grade='{self.grade.value}')>"