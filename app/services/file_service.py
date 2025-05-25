import os
import uuid
import shutil
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
from app.config import settings


class FileService:

    @staticmethod
    def get_allowed_extensions():
        """Получить разрешенные расширения файлов"""
        return settings.ALLOWED_EXTENSIONS or ['jpg', 'jpeg', 'png', 'webp']

    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Валидация загружаемого файла"""
        # Проверка размера файла
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл слишком большой. Максимальный размер: {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        # Проверка расширения файла
        if file.filename:
            extension = file.filename.split('.')[-1].lower()
            if extension not in FileService.get_allowed_extensions():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(FileService.get_allowed_extensions())}"
                )

    @staticmethod
    def generate_filename(original_filename: str) -> str:
        """Генерация уникального имени файла"""
        extension = original_filename.split('.')[-1].lower()
        unique_name = f"{uuid.uuid4()}.{extension}"
        return unique_name

    @staticmethod
    def ensure_directory_exists(directory: str) -> None:
        """Создание директории если она не существует"""
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    async def save_product_image(file: UploadFile, is_main: bool = False) -> str:
        """
        Сохранение изображения товара

        Args:
            file: Загружаемый файл
            is_main: Является ли изображение основным

        Returns:
            str: Путь к сохраненному файлу
        """
        # Валидация файла
        FileService.validate_file(file)

        # Генерация имени файла
        filename = FileService.generate_filename(file.filename)

        # Создание пути для сохранения
        upload_dir = os.path.join(settings.UPLOAD_DIR, "products")
        FileService.ensure_directory_exists(upload_dir)

        file_path = os.path.join(upload_dir, filename)

        try:
            # Сохранение файла
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Обработка изображения (изменение размера, оптимизация)
            FileService.process_image(file_path, is_main)

            # Возвращаем относительный путь для БД
            return f"products/{filename}"

        except Exception as e:
            # Удаляем файл в случае ошибки
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при сохранении файла: {str(e)}"
            )

    @staticmethod
    def process_image(file_path: str, is_main: bool = False) -> None:
        """
        Обработка изображения (изменение размера, оптимизация)

        Args:
            file_path: Путь к файлу
            is_main: Является ли изображение основным
        """
        try:
            with Image.open(file_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Определяем размеры в зависимости от типа изображения
                if is_main:
                    # Основное изображение - больше размер
                    max_size = (800, 800)
                else:
                    # Дополнительные изображения - меньше размер
                    max_size = (600, 600)

                # Изменяем размер с сохранением пропорций
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Сохраняем с оптимизацией
                img.save(file_path, optimize=True, quality=85)

        except Exception as e:
            print(f"Ошибка обработки изображения {file_path}: {str(e)}")

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Удаление файла

        Args:
            file_path: Относительный путь к файлу

        Returns:
            bool: True если файл удален успешно
        """
        try:
            full_path = os.path.join(settings.UPLOAD_DIR, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления файла {file_path}: {str(e)}")
            return False

    @staticmethod
    def get_file_url(file_path: Optional[str]) -> Optional[str]:
        """
        Получение URL файла для фронтенда

        Args:
            file_path: Относительный путь к файлу

        Returns:
            str: URL файла или None
        """
        if not file_path:
            return None

        return f"/static/uploads/{file_path}"

    @staticmethod
    async def save_multiple_images(files: List[UploadFile]) -> List[str]:
        """
        Сохранение нескольких изображений

        Args:
            files: Список файлов для загрузки

        Returns:
            List[str]: Список путей к сохраненным файлам
        """
        saved_files = []

        try:
            for file in files:
                file_path = await FileService.save_product_image(file, is_main=False)
                saved_files.append(file_path)

            return saved_files

        except Exception as e:
            # В случае ошибки удаляем уже загруженные файлы
            for file_path in saved_files:
                FileService.delete_file(file_path)
            raise e