"""Конфигурация приложения.

Все настройки читаются из переменных окружения (фактор III «Конфигурация»
методологии 12 факторов). Секреты в коде не хранятся: если JWT_SECRET_KEY
не задан в окружении, приложение падает при старте (fail-fast).

Локально переменные можно положить в файл backend/.env (см. .env.example),
в Docker — через environment/env_file в docker-compose.yml.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, собранные из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Строка подключения к PostgreSQL (фактор IV — подключаемый ресурс).
    database_url: str = (
        "postgresql+psycopg://shiftplanner:shiftplanner@localhost:5432/shiftplanner"
    )

    # Секрет для подписи JWT. Значения по умолчанию нет намеренно:
    # без явно заданного секрета приложение не должно стартовать.
    jwt_secret_key: str

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Список разрешённых источников для CORS (через запятую).
    # Нужен только для локальной разработки фронтенда (vite dev-server);
    # в Docker фронтенд и API обслуживаются с одного origin через nginx.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Возвращает кешированный объект настроек (читаем env один раз)."""
    return Settings()
