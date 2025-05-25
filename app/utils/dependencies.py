from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.utils.exceptions import AuthException

# Схема безопасности для Bearer токенов
security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    Зависимость для получения текущего авторизованного пользователя
    """
    token = credentials.credentials
    email = AuthService.verify_token(token)

    if email is None:
        raise AuthException.INVALID_TOKEN

    user = AuthService.get_user_by_email(db, email=email)
    if user is None:
        raise AuthException.INVALID_TOKEN

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Зависимость для получения активного пользователя
    """
    if not current_user.is_active:
        raise AuthException.INACTIVE_USER
    return current_user


async def get_current_admin_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Зависимость для получения пользователя с правами администратора
    """
    if not current_user.is_admin:
        raise AuthException.PERMISSION_DENIED
    return current_user


# Опциональная авторизация (для случаев, когда пользователь может быть не авторизован)
async def get_current_user_optional(
        db: Session = Depends(get_db),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Зависимость для получения пользователя (если авторизован) или None
    """
    if credentials is None:
        return None

    token = credentials.credentials
    email = AuthService.verify_token(token)

    if email is None:
        return None

    user = AuthService.get_user_by_email(db, email=email)
    return user if user and user.is_active else None