from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создание движка базы данных
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Логирование SQL запросов (отключи в продакшене)
    pool_pre_ping=True,  # Проверка соединения
    pool_recycle=300,    # Переподключение каждые 5 минут
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()