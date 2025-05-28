from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User
from pydantic import EmailStr


''' Контекст для хеширования паролей '''
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


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


    ''' Аутентификация пользователя '''
    @staticmethod
    def authenticate_user(db: Session, email: Str, password: str) -> Type[User] | None:
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