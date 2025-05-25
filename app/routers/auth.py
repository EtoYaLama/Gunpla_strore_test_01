from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, UserProfile, UserUpdate
from app.utils.dependencies import get_current_active_user, get_current_user
from app.utils.exceptions import AuthException
from app.config import settings
from app.models import User

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
    # Проверяем, что пользователь с таким email не существует
    if AuthService.get_user_by_email(db, email=user.email):
        raise AuthException.USER_ALREADY_EXISTS

    # Проверяем, что username не занят
    if AuthService.get_user_by_username(db, username=user.username):
        raise AuthException.USERNAME_TAKEN

    # Создаем пользователя
    db_user = AuthService.create_user(
        db=db,
        email=user.email,
        username=user.username,
        password=user.password,
        full_name=user.full_name
    )

    return db_user


@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Авторизация пользователя
    """
    user = AuthService.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise AuthException.INVALID_CREDENTIALS

    if not user.is_active:
        raise AuthException.INACTIVE_USER

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Альтернативный эндпоинт для OAuth2PasswordRequestForm (для FastAPI docs)
@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    Авторизация через OAuth2 форму (для Swagger UI)
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise AuthException.INVALID_CREDENTIALS

    if not user.is_active:
        raise AuthException.INACTIVE_USER

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Получение профиля текущего пользователя
    """
    return current_user


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Обновление профиля текущего пользователя
    """
    # Обновляем поля
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.address is not None:
        current_user.address = user_update.address

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Проверка действительности токена
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }