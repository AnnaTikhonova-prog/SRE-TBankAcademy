"""Зависимости FastAPI: извлечение текущего пользователя и проверка ролей."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.security import JWTError, decode_access_token

# tokenUrl используется только Swagger UI для кнопки Authorize.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Стандартный ответ 401 с заголовком WWW-Authenticate (по RFC 6750).
CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Не удалось проверить учётные данные",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Декодирует JWT и возвращает пользователя из БД."""
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise CREDENTIALS_ERROR

    user = db.get(models.User, user_id)
    if user is None:
        raise CREDENTIALS_ERROR
    return user


def require_manager(user: models.User = Depends(get_current_user)) -> models.User:
    """Пропускает только менеджеров."""
    if user.role != "manager":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Требуется роль менеджера")
    return user


def require_employee(user: models.User = Depends(get_current_user)) -> models.User:
    """Пропускает только сотрудников."""
    if user.role != "employee":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Требуется роль сотрудника")
    return user


def get_manager_company(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_manager),
) -> models.Company:
    """Возвращает компанию, которой владеет текущий менеджер."""
    company = (
        db.query(models.Company)
        .filter(models.Company.manager_id == user.id)
        .first()
    )
    if company is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Сначала создайте компанию",
        )
    return company


def get_current_employee(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_employee),
) -> models.Employee:
    """Возвращает профиль сотрудника текущего пользователя."""
    employee = (
        db.query(models.Employee)
        .filter(models.Employee.user_id == user.id)
        .first()
    )
    if employee is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Вы ещё не присоединились к компании по коду приглашения",
        )
    return employee
