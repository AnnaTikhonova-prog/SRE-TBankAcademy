"""Компании: создание менеджером, просмотр, вступление сотрудника по коду."""

import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, get_manager_company, require_employee, require_manager

router = APIRouter()

# Алфавит кода приглашения: без похожих символов (0/O, 1/I), чтобы код
# было удобно диктовать сотрудникам голосом.
_INVITE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_invite_code(db: Session, length: int = 8) -> str:
    """Генерирует уникальный код приглашения компании."""
    for _ in range(10):
        code = "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(length))
        exists = db.query(models.Company).filter(models.Company.invite_code == code).first()
        if exists is None:
            return code
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Не удалось сгенерировать код приглашения",
    )


@router.post(
    "/",
    response_model=schemas.CompanyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    payload: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_manager),
):
    """Менеджер создаёт свою компанию (у менеджера может быть одна компания)."""
    existing = (
        db.query(models.Company).filter(models.Company.manager_id == user.id).first()
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Компания уже создана")

    company = models.Company(
        name=payload.name,
        address=payload.address,
        invite_code=_generate_invite_code(db),
        manager_id=user.id,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/my", response_model=schemas.CompanyRead)
def get_my_company(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Компания текущего пользователя (менеджера или сотрудника)."""
    if user.role == "manager":
        company = (
            db.query(models.Company).filter(models.Company.manager_id == user.id).first()
        )
    else:
        employee = (
            db.query(models.Employee).filter(models.Employee.user_id == user.id).first()
        )
        company = db.get(models.Company, employee.company_id) if employee else None

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return company


@router.patch("/my", response_model=schemas.CompanyRead)
def update_my_company(
    payload: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    """Менеджер обновляет название/адрес своей компании.
    null для address очищает адрес (учитываем только явно переданные поля)."""
    if payload.name is not None:
        company.name = payload.name
    if "address" in payload.model_fields_set:
        company.address = payload.address
    db.commit()
    db.refresh(company)
    return company


@router.post(
    "/join",
    response_model=schemas.EmployeeBrief,
    status_code=status.HTTP_201_CREATED,
)
def join_company(
    payload: schemas.JoinCompanyRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_employee),
):
    """Сотрудник вступает в компанию по коду приглашения."""
    already = db.query(models.Employee).filter(models.Employee.user_id == user.id).first()
    if already is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Вы уже состоите в компании",
        )

    company = (
        db.query(models.Company)
        .filter(models.Company.invite_code == payload.invite_code.strip().upper())
        .first()
    )
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Неверный код приглашения")

    employee = models.Employee(user_id=user.id, company_id=company.id)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
