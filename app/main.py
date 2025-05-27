from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth
from app.routers import orders
from app.routers import products
from app.routers import reviews
from app.routers.history import router as history_router, favorites_router
from app.config import settings


# Создание приложения FastAPI
app = FastAPI(
    title="Gunpla Store API",
    description="API для интернет-магазина моделей Gunpla",
    version="1.0.0"
)

# Подключение статических файлов
# app.mount("/node", StaticFiles(directory="app/static"), name="static")

# Подключение роутеров
app.include_router(auth.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(history_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Gunpla Store API!"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}