"""Подключение к базе данных PostgreSQL.

Движок SQLAlchemy создаётся один раз на процесс; сессии выдаются
через зависимость FastAPI `get_db` и закрываются после каждого запроса.
Приложение не хранит состояние между запросами (фактор VI — процессы
без состояния), всё состояние живёт в PostgreSQL.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# pool_pre_ping=True — перед выдачей соединения из пула проверяем,
# что оно живо (полезно после рестартов БД).
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI: выдаёт сессию БД на время запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
