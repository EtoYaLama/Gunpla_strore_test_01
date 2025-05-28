from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User
from app.database import get_db


''' Контекст для хеширования паролей '''
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


''' Настройка OAuth2PasswordBearer для получения токена из заголовков '''
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



class AuthService:
    """ Проверка пароля """
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)


    ''' Хеширование пароля '''
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)


    ''' Создание JWT токена '''
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({'exp': expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt


    ''' Проверка JWT токена и извлечение email '''
    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get('sub')
            if email is None:
                return None
            return email
        except JWTError:
            return None


    @staticmethod
    def decode_token(token: str) -> Optional[int]:
        """Декодирование и проверка JWT токена"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: int = payload.get("sub")
            if user_id is None:
                raise ValueError("User ID отсутствует в токене")
            return user_id
        except JWTError:
            return None


    @staticmethod
    def get_user_from_db(db: Session, user_id: int) -> Optional[User]:
        """Получение пользователя из базы данных по ID"""
        return db.query(User).filter(and_(User.id == user_id)).first()


    ''' Аутентификация пользователя '''
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> type[User] | None:
        user = db.query(User).filter(and_(User.email == email)).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user


    ''' Получение пользователя по email '''
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(and_(User.email == email)).first()


    ''' Получение пользователя по username '''
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(and_(User.username == username)).first()


    ''' Создание нового пользователя '''
    @staticmethod
    def create_user(db: Session, email: str, username: str, password: str, full_name: str = None) -> User:
        hashed_password = AuthService.get_password_hash(password)
        db_user = User(
            email=email,
            username=username,
            password_hash=hashed_password,
            full_name=full_name,
            is_admin=False,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
    """Получение текущего пользователя на основе токена"""
    user_id = AuthService.decode_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен авторизации",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = AuthService.get_user_from_db(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    return user


def get_current_admin_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Получение текущего пользователя-администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа. Требуются права администратора",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт администратора неактивен",
        )

    return current_user