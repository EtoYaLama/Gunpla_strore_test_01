from fastapi import HTTPException, status


class AuthException:
    INVALID_CREDENTIALS = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный email или пароль",
        headers={"WWW-Authenticate": "Bearer"},
    )

    INVALID_TOKEN = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный токен авторизации",
        headers={"WWW-Authenticate": "Bearer"},
    )

    INACTIVE_USER = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Неактивный пользователь"
    )

    USER_ALREADY_EXISTS = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Пользователь с таким email уже существует"
    )

    USERNAME_TAKEN = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Имя пользователя уже занято"
    )

    PERMISSION_DENIED = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Недостаточно прав доступа"
    )


class AdminServiceException(Exception):
    """Базовое исключение для административного сервиса"""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Преобразование в HTTPException для FastAPI"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.message
        )

    # Предопределенные исключения для частых случаев
    @classmethod
    def user_not_found(cls) -> "AdminServiceException":
        return cls("Пользователь не найден", status.HTTP_404_NOT_FOUND)

    @classmethod
    def product_not_found(cls) -> "AdminServiceException":
        return cls("Товар не найден", status.HTTP_404_NOT_FOUND)

    @classmethod
    def order_not_found(cls) -> "AdminServiceException":
        return cls("Заказ не найден", status.HTTP_404_NOT_FOUND)

    @classmethod
    def review_not_found(cls) -> "AdminServiceException":
        return cls("Отзыв не найден", status.HTTP_404_NOT_FOUND)

    @classmethod
    def cannot_delete_product_with_orders(cls) -> "AdminServiceException":
        return cls(
            "Нельзя удалить товар с активными заказами. Дождитесь завершения всех заказов.",
            status.HTTP_409_CONFLICT
        )

    @classmethod
    def invalid_order_status(cls, status_name: str) -> "AdminServiceException":
        return cls(
            f"Недопустимый статус заказа: {status_name}",
            status.HTTP_400_BAD_REQUEST
        )

    @classmethod
    def database_error(cls, error_msg: str) -> "AdminServiceException":
        return cls(
            f"Ошибка базы данных: {error_msg}",
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @classmethod
    def insufficient_stock(cls, product_name: str = None) -> "AdminServiceException":
        detail = f"Недостаточно товара на складе" + (f": {product_name}" if product_name else "")
        return cls(detail, status.HTTP_409_CONFLICT)

    @classmethod
    def invalid_data(cls, field_name: str = None) -> "AdminServiceException":
        detail = f"Некорректные данные" + (f" в поле: {field_name}" if field_name else "")
        return cls(detail, status.HTTP_422_UNPROCESSABLE_ENTITY)