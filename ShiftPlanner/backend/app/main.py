"""Точка входа FastAPI-приложения ShiftPlanner (учебная версия).

Запуск: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import SessionLocal
from app.routers import auth, availability, branches, companies, employees, positions, shifts

# Фактор XI: логи пишем в stdout, их забирает docker logs / оркестратор.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("shiftplanner")

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Хук жизненного цикла: логируем старт и остановку приложения."""
    logger.info("ShiftPlanner API запущен")
    yield
    logger.info("ShiftPlanner API остановлен")


app = FastAPI(
    title="ShiftPlanner API",
    version="1.0.0",
    description="Учебная версия ShiftPlanner: JWT-аутентификация и CRUD для планирования смен.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
app.include_router(companies.router, prefix="/companies", tags=["Компании"])
app.include_router(branches.router, prefix="/branches", tags=["Филиалы"])
app.include_router(positions.router, prefix="/positions", tags=["Должности"])
app.include_router(employees.router, prefix="/employees", tags=["Сотрудники"])
app.include_router(availability.router, prefix="/availability", tags=["Доступность"])
app.include_router(shifts.router, prefix="/shifts", tags=["Смены"])


@app.get("/health", tags=["Служебные"])
def health_check():
    """Liveness-проба: процесс жив и обслуживает запросы."""
    return {"status": "ok"}


@app.get("/health/db", tags=["Служебные"])
def database_health_check():
    """Readiness-проба: проверяет доступность PostgreSQL."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except SQLAlchemyError:
        logger.exception("Проверка соединения с БД не удалась")
        return JSONResponse(status_code=503, content={"status": "error"})
