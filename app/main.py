from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth
from app.config import settings

# Создание приложения FastAPI
app = FastAPI(
    title="Gunpla Store API",
    description="API для интернет-магазина моделей Gunpla",
    version="1.0.0"
)

# Подключение статических файлов
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключение роутеров
app.include_router(auth.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Gunpla Store API!"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}