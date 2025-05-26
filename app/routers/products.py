from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import uuid

from ..database import get_db
from ..models.product import Product, Grade
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse
from ..services.file_service import file_service
from ..utils.dependencies import get_current_admin_user
from ..models.user import User

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=dict)
async def get_products(
        page: int = Query(1, ge=1, description="Номер страницы"),
        limit: int = Query(10, ge=1, le=50, description="Количество товаров на странице"),
        search: Optional[str] = Query(None, description="Поиск по названию"),
        grade: Optional[Grade] = Query(None, description="Фильтр по грейду"),
        manufacturer: Optional[str] = Query(None, description="Фильтр по производителю"),
        series: Optional[str] = Query(None, description="Фильтр по серии"),
        min_price: Optional[float] = Query(None, ge=0, description="Минимальная цена"),
        max_price: Optional[float] = Query(None, ge=0, description="Максимальная цена"),
        in_stock_only: bool = Query(False, description="Только товары в наличии"),
        sort_by: str = Query("created_at", description="Сортировка: name, price, rating, created_at"),
        sort_order: str = Query("desc", description="Порядок: asc, desc"),
        db: Session = Depends(get_db)
):
    """Получение списка товаров с фильтрацией и пагинацией"""

    # Базовый запрос
    query = db.query(Product)

    # Применяем фильтры
    filters = []

    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.series.ilike(f"%{search}%")
            )
        )

    if grade:
        filters.append(Product.grade == grade)

    if manufacturer:
        filters.append(Product.manufacturer.ilike(f"%{manufacturer}%"))

    if series:
        filters.append(Product.series.ilike(f"%{series}%"))

    if min_price is not None:
        filters.append(Product.price >= min_price)

    if max_price is not None:
        filters.append(Product.price <= max_price)

    if in_stock_only:
        filters.append(Product.in_stock > 0)

    # Применяем все фильтры
    if filters:
        query = query.filter(and_(*filters))

    # Сортировка
    if sort_by == "name":
        order_column = Product.name
    elif sort_by == "price":
        order_column = Product.price
    elif sort_by == "rating":
        order_column = Product.average_rating
    else:
        order_column = Product.created_at

    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    # Подсчет общего количества
    total_count = query.count()

    # Пагинация
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()

    # Формируем ответ
    return {
        "products": [
            {
                **ProductResponse.from_orm(product).dict(),
                "main_image_url": file_service.get_image_url(product.main_image),
                "thumbnail_url": file_service.get_image_url(product.main_image, "thumbnail")
            }
            for product in products
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "has_next": page * limit < total_count,
            "has_prev": page > 1
        },
        "filters": {
            "search": search,
            "grade": grade,
            "manufacturer": manufacturer,
            "series": series,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock_only": in_stock_only,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }


@router.get("/{product_id}", response_model=dict)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Получение товара по ID"""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID товара")

    product = db.query(Product).filter(product_uuid == Product.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Формируем URLs для изображений
    additional_images = []
    if product.additional_images:
        for img in product.additional_images:
            additional_images.append({
                "thumbnail": file_service.get_image_url(img, "thumbnail"),
                "medium": file_service.get_image_url(img, "medium"),
                "large": file_service.get_image_url(img, "large")
            })

    product_data = ProductResponse.from_orm(product).dict()
    product_data.update({
        "main_image_url": file_service.get_image_url(product.main_image, "large"),
        "main_image_thumbnail": file_service.get_image_url(product.main_image, "thumbnail"),
        "additional_images_urls": additional_images
    })

    return product_data


@router.post("/", response_model=ProductResponse)
async def create_product(
        name: str = Form(...),
        description: str = Form(...),
        price: float = Form(..., ge=0),
        grade: Grade = Form(...),
        manufacturer: str = Form(...),
        series: str = Form(...),
        scale: str = Form(...),
        difficulty: int = Form(..., ge=1, le=5),
        in_stock: int = Form(..., ge=0),
        main_image: UploadFile = File(...),
        additional_images: List[UploadFile] = File(default=[]),
        current_admin: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Создание нового товара (только для админов)"""

    # Сохраняем изображения
    all_images = [main_image] + additional_images
    saved_images = await file_service.save_product_images(all_images)

    if not saved_images:
        raise HTTPException(status_code=400, detail="Не удалось сохранить изображения")

    # Создаем товар
    product_data = {
        "name": name,
        "description": description,
        "price": price,
        "grade": grade,
        "manufacturer": manufacturer,
        "series": series,
        "scale": scale,
        "difficulty": difficulty,
        "in_stock": in_stock,
        "main_image": saved_images[0],
        "additional_images": saved_images[1:] if len(saved_images) > 1 else []
    }

    product = Product(**product_data)
    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
        product_id: str,
        name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None, ge=0),
        grade: Optional[Grade] = Form(None),
        manufacturer: Optional[str] = Form(None),
        series: Optional[str] = Form(None),
        scale: Optional[str] = Form(None),
        difficulty: Optional[int] = Form(None, ge=1, le=5),
        in_stock: Optional[int] = Form(None, ge=0),
        main_image: Optional[UploadFile] = File(None),
        additional_images: List[UploadFile] = File(default=[]),
        current_admin: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Обновление товара (только для админов)"""

    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID товара")

    product = db.query(Product).filter(product_uuid == Product.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Обновляем поля
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if price is not None:
        update_data["price"] = price
    if grade is not None:
        update_data["grade"] = grade
    if manufacturer is not None:
        update_data["manufacturer"] = manufacturer
    if series is not None:
        update_data["series"] = series
    if scale is not None:
        update_data["scale"] = scale
    if difficulty is not None:
        update_data["difficulty"] = difficulty
    if in_stock is not None:
        update_data["in_stock"] = in_stock

    # Обновляем изображения если они переданы
    if main_image or additional_images:
        # Удаляем старые изображения
        old_images = [product.main_image] + (product.additional_images or [])
        file_service.delete_product_images([img for img in old_images if img])

        # Сохраняем новые
        new_images = []
        if main_image:
            new_images.append(main_image)
        new_images.extend(additional_images)

        saved_images = await file_service.save_product_images(new_images)

        if saved_images:
            update_data["main_image"] = saved_images[0]
            update_data["additional_images"] = saved_images[1:] if len(saved_images) > 1 else []

    # Применяем обновления
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}")
async def delete_product(
        product_id: str,
        current_admin: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Удаление товара (только для админов)"""

    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID товара")

    product = db.query(Product).filter(product_uuid == Product.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Удаляем изображения
    images_to_delete = [product.main_image] + (product.additional_images or [])
    file_service.delete_product_images([img for img in images_to_delete if img])

    # Удаляем товар
    db.delete(product)
    db.commit()

    return {"message": "Товар успешно удален"}


@router.get("/filters/options")
async def get_filter_options(db: Session = Depends(get_db)):
    """Получение опций для фильтров"""

    # Получаем уникальные значения для фильтров
    manufacturers = db.query(Product.manufacturer).distinct().all()
    series = db.query(Product.series).distinct().all()
    grades = [grade.value for grade in Grade]

    # Получаем диапазон цен
    price_range = db.query(
        db.func.min(Product.price).label('min_price'),
        db.func.max(Product.price).label('max_price')
    ).first()

    return {
        "manufacturers": [m[0] for m in manufacturers if m[0]],
        "series": [s[0] for s in series if s[0]],
        "grades": grades,
        "price_range": {
            "min": float(price_range.min_price) if price_range.min_price else 0,
            "max": float(price_range.max_price) if price_range.max_price else 0
        }
    }