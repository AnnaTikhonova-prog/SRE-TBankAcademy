"""Аутентификация: регистрация, вход, профиль текущего пользователя.

JWT полностью stateless: сервер не хранит выданные токены и сессии,
поэтому выход из аккаунта выполняется на клиенте (удалением токена),
а экземпляры бэкенда остаются взаимозаменяемыми.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user
from app.security import create_access_token, get_password_hash, verify_password

router = APIRouter()


def _build_user_read(db: Session, user: models.User) -> schemas.UserRead:
    """Собирает профиль пользователя с компанией и профилем сотрудника."""
    company = None
    employee = None

    if user.role == "manager":
        company = (
            db.query(models.Company)
            .filter(models.Company.manager_id == user.id)
            .first()
        )
    else:
        employee = (
            db.query(models.Employee)
            .filter(models.Employee.user_id == user.id)
            .first()
        )
        if employee is not None:
            company = db.get(models.Company, employee.company_id)

    return schemas.UserRead(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        company=schemas.CompanyBrief.model_validate(company) if company else None,
        employee=schemas.EmployeeBrief.model_validate(employee) if employee else None,
    )


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Регистрация нового пользователя (менеджера или сотрудника)."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_user_read(db, user)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Вход по email и паролю, возвращает JWT."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    token = create_access_token(subject=str(user.id), role=user.role)
    return schemas.TokenResponse(access_token=token, role=user.role)


@router.post("/token", response_model=schemas.TokenResponse, include_in_schema=False)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Тот же вход через OAuth2-форму — нужен кнопке Authorize в Swagger UI."""
    return login(
        schemas.LoginRequest(email=form_data.username, password=form_data.password),
        db,
    )


@router.get("/me", response_model=schemas.UserRead)
def get_me(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Профиль текущего пользователя по JWT."""
    return _build_user_read(db, user)
