"""Смены: менеджер назначает и редактирует, сотрудник смотрит свои.

В исходной (боевой) версии ShiftPlanner расписание генерировалось
автоматически солвером OR-Tools. В учебной версии солвер убран как
избыточно сложный: назначение смен — обычные CRUD-операции менеджера.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, get_manager_company

router = APIRouter()


def _to_shift_read(shift: models.Shift) -> schemas.ShiftRead:
    return schemas.ShiftRead(
        id=shift.id,
        shift_date=shift.shift_date,
        start_time=shift.start_time,
        end_time=shift.end_time,
        branch_id=shift.branch_id,
        branch_name=shift.branch.name,
        position_id=shift.position_id,
        position_name=shift.position.name,
        employee_id=shift.employee_id,
        employee_name=shift.employee.user.full_name,
    )


def _check_overlap(
    db: Session,
    employee_id: int,
    shift_date: date,
    start_time,
    end_time,
    exclude_shift_id: int | None = None,
) -> None:
    """Запрещает пересекающиеся смены одного сотрудника в один день."""
    query = db.query(models.Shift).filter(
        models.Shift.employee_id == employee_id,
        models.Shift.shift_date == shift_date,
        models.Shift.start_time < end_time,
        models.Shift.end_time > start_time,
    )
    if exclude_shift_id is not None:
        query = query.filter(models.Shift.id != exclude_shift_id)
    if query.first() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Смена пересекается по времени с другой сменой сотрудника",
        )


def _validate_refs(
    db: Session,
    company_id: int,
    branch_id: int,
    position_id: int,
    employee_id: int,
) -> None:
    """Проверяет, что филиал, должность и сотрудник — из компании менеджера."""
    branch = db.get(models.Branch, branch_id)
    if branch is None or branch.company_id != company_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Филиал не из этой компании")

    position = db.get(models.Position, position_id)
    if position is None or position.company_id != company_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Должность не из этой компании")

    employee = db.get(models.Employee, employee_id)
    if employee is None or employee.company_id != company_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Сотрудник не из этой компании")
    if not employee.is_active:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Сотрудник деактивирован",
        )


@router.get("/", response_model=list[schemas.ShiftRead])
def list_shifts(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Список смен за период.

    Менеджер видит все смены своей компании, сотрудник — только свои.
    """
    query = db.query(models.Shift)

    if user.role == "manager":
        company = (
            db.query(models.Company).filter(models.Company.manager_id == user.id).first()
        )
        if company is None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Сначала создайте компанию")
        query = query.filter(models.Shift.company_id == company.id)
    else:
        employee = (
            db.query(models.Employee).filter(models.Employee.user_id == user.id).first()
        )
        if employee is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Вы ещё не присоединились к компании",
            )
        query = query.filter(models.Shift.employee_id == employee.id)

    if date_from is not None:
        query = query.filter(models.Shift.shift_date >= date_from)
    if date_to is not None:
        query = query.filter(models.Shift.shift_date <= date_to)

    shifts = query.order_by(models.Shift.shift_date, models.Shift.start_time).all()
    return [_to_shift_read(s) for s in shifts]


@router.post("/", response_model=schemas.ShiftRead, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: schemas.ShiftCreate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    _validate_refs(db, company.id, payload.branch_id, payload.position_id, payload.employee_id)
    _check_overlap(db, payload.employee_id, payload.shift_date, payload.start_time, payload.end_time)

    shift = models.Shift(
        company_id=company.id,
        branch_id=payload.branch_id,
        position_id=payload.position_id,
        employee_id=payload.employee_id,
        shift_date=payload.shift_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return _to_shift_read(shift)


def _get_shift_or_404(db: Session, company_id: int, shift_id: int) -> models.Shift:
    shift = db.get(models.Shift, shift_id)
    if shift is None or shift.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Смена не найдена")
    return shift


@router.get("/{shift_id}", response_model=schemas.ShiftRead)
def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    return _to_shift_read(_get_shift_or_404(db, company.id, shift_id))


@router.patch("/{shift_id}", response_model=schemas.ShiftRead)
def update_shift(
    shift_id: int,
    payload: schemas.ShiftUpdate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    shift = _get_shift_or_404(db, company.id, shift_id)

    new_branch_id = payload.branch_id if payload.branch_id is not None else shift.branch_id
    new_position_id = payload.position_id if payload.position_id is not None else shift.position_id
    new_employee_id = payload.employee_id if payload.employee_id is not None else shift.employee_id
    new_date = payload.shift_date if payload.shift_date is not None else shift.shift_date
    new_start = payload.start_time if payload.start_time is not None else shift.start_time
    new_end = payload.end_time if payload.end_time is not None else shift.end_time

    if new_end <= new_start:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time должен быть позже start_time",
        )

    _validate_refs(db, company.id, new_branch_id, new_position_id, new_employee_id)
    _check_overlap(db, new_employee_id, new_date, new_start, new_end, exclude_shift_id=shift.id)

    shift.branch_id = new_branch_id
    shift.position_id = new_position_id
    shift.employee_id = new_employee_id
    shift.shift_date = new_date
    shift.start_time = new_start
    shift.end_time = new_end
    db.commit()
    db.refresh(shift)
    return _to_shift_read(shift)


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    shift = _get_shift_or_404(db, company.id, shift_id)
    db.delete(shift)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
