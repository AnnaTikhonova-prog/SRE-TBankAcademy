"""Безопасность: хеширование паролей (bcrypt) и выпуск/проверка JWT.

Используем bcrypt напрямую, без passlib, — меньше зависимостей и нет
проблем совместимости версий. JWT stateless: сервер не хранит сессии,
поэтому экземпляры бэкенда можно свободно масштабировать (факторы VI и VIII).
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def get_password_hash(password: str) -> str:
    """Возвращает bcrypt-хеш пароля (храним только хеш, никогда сам пароль)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверяет пароль против сохранённого хеша."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, role: str) -> str:
    """Выпускает подписанный JWT с идентификатором пользователя и его ролью."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Декодирует и проверяет JWT. Бросает JWTError при невалидном токене."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]
