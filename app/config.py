from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, List
from dotenv import find_dotenv

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File uploads
    UPLOAD_DIR: str = "app/static/uploads"
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 12
    MAX_PAGE_SIZE: int = 100

    CLICK_SERVICE_ID: Optional[str]
    CLICK_SECRET_KEY: Optional[str]
    PAYME_MERCHANT_ID: Optional[str]
    PAYME_SECRET_KEY: Optional[str]
    UPLOAD_FOLDER: Optional[str] = "static/uploads"
    ALLOWED_EXTENSIONS: Optional[List[str]]
    SMTP_HOST: Optional[str]
    SMTP_PORT: Optional[int]
    SMTP_USER: Optional[str]
    SMTP_PASSWORD: Optional[str]
    ENVIRONMENT: Optional[str] = "development"
    DEBUG: Optional[bool] = True

    # Для обслуживания статических файлов
    STATIC_URL: str = "/static"
    STATIC_DIR: str = "app/static"

    # Validator для преобразования строки в список
    @validator("ALLOWED_EXTENSIONS", pre=True, always=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    class Config:
        env_file = find_dotenv()

try:
    settings = Settings()
except ValidationError as e:
    print(f"Ошибка загрузки переменных окружения: {e}")
    exit(1)