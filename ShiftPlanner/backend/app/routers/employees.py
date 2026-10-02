"""Сотрудники компании: просмотр и управление (менеджер), свой профиль (сотрудник)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_manager_company

router = APIRouter()


def _to_employee_read(employee: models.Employee) -> schemas.EmployeeRead:
    return schemas.EmployeeRead(
        id=employee.id,
        full_name=employee.user.full_name,
        email=employee.user.email,
        branch_id=employee.branch_id,
        branch_name=employee.branch.name if employee.branch else None,
        position_id=employee.position_id,
        position_name=employee.position.name if employee.position else None,
        is_active=employee.is_active,
    )


def _get_employee_or_404(db: Session, company_id: int, employee_id: int) -> models.Employee:
    employee = db.get(models.Employee, employee_id)
    if employee is None or employee.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Сотрудник не найден")
    return employee


@router.get("/", response_model=list[schemas.EmployeeRead])
def list_employees(company: models.Company = Depends(get_manager_company)):
    """Все сотрудники компании менеджера."""
    return [_to_employee_read(e) for e in sorted(company.employees, key=lambda x: x.id)]


@router.get("/{employee_id}", response_model=schemas.EmployeeRead)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    return _to_employee_read(_get_employee_or_404(db, company.id, employee_id))


@router.get("/{employee_id}/availability", response_model=list[schemas.AvailabilityRead])
def get_employee_availability(
    employee_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    """Недельная доступность сотрудника — менеджер сверяется с ней,
    когда назначает смены."""
    employee = _get_employee_or_404(db, company.id, employee_id)
    return sorted(employee.availability, key=lambda a: (a.weekday, a.start_time))


@router.patch("/{employee_id}", response_model=schemas.EmployeeRead)
def update_employee(
    employee_id: int,
    payload: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    """Менеджер назначает сотруднику филиал/должность или деактивирует его.

    Учитываются только поля, явно переданные в запросе (model_fields_set):
    так `null` сбрасывает филиал/должность, а отсутствие поля — «не менять».
    """
    employee = _get_employee_or_404(db, company.id, employee_id)
    fields = payload.model_fields_set

    if "branch_id" in fields:
        if payload.branch_id is not None:
            branch = db.get(models.Branch, payload.branch_id)
            if branch is None or branch.company_id != company.id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Филиал не из этой компании")
        employee.branch_id = payload.branch_id

    if "position_id" in fields:
        if payload.position_id is not None:
            position = db.get(models.Position, payload.position_id)
            if position is None or position.company_id != company.id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Должность не из этой компании")
        employee.position_id = payload.position_id

    if "is_active" in fields and payload.is_active is not None:
        employee.is_active = payload.is_active

    db.commit()
    db.refresh(employee)
    return _to_employee_read(employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    """Удаляет профиль сотрудника из компании.

    Учётная запись пользователя сохраняется: он может снова вступить
    в компанию по коду приглашения. Его смены и доступность удаляются
    каскадно на уровне БД.
    """
    employee = _get_employee_or_404(db, company.id, employee_id)
    db.delete(employee)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
