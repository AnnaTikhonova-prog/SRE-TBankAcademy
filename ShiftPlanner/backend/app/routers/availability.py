"""Доступность сотрудника: когда он может работать (CRUD для самого сотрудника)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_employee

router = APIRouter()


def _get_block_or_404(db: Session, employee_id: int, block_id: int) -> models.EmployeeAvailability:
    block = db.get(models.EmployeeAvailability, block_id)
    if block is None or block.employee_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Интервал не найден")
    return block


@router.get("/my", response_model=list[schemas.AvailabilityRead])
def list_my_availability(employee: models.Employee = Depends(get_current_employee)):
    return sorted(employee.availability, key=lambda a: (a.weekday, a.start_time))


@router.post("/", response_model=schemas.AvailabilityRead, status_code=status.HTTP_201_CREATED)
def create_availability(
    payload: schemas.AvailabilityCreate,
    db: Session = Depends(get_db),
    employee: models.Employee = Depends(get_current_employee),
):
    block = models.EmployeeAvailability(
        employee_id=employee.id,
        weekday=payload.weekday,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(block)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Такой интервал уже существует",
        )
    db.refresh(block)
    return block


@router.patch("/{block_id}", response_model=schemas.AvailabilityRead)
def update_availability(
    block_id: int,
    payload: schemas.AvailabilityUpdate,
    db: Session = Depends(get_db),
    employee: models.Employee = Depends(get_current_employee),
):
    block = _get_block_or_404(db, employee.id, block_id)

    new_weekday = payload.weekday if payload.weekday is not None else block.weekday
    new_start = payload.start_time if payload.start_time is not None else block.start_time
    new_end = payload.end_time if payload.end_time is not None else block.end_time
    if new_end <= new_start:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time должен быть позже start_time",
        )

    block.weekday = new_weekday
    block.start_time = new_start
    block.end_time = new_end
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Такой интервал уже существует",
        )
    db.refresh(block)
    return block


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(
    block_id: int,
    db: Session = Depends(get_db),
    employee: models.Employee = Depends(get_current_employee),
):
    block = _get_block_or_404(db, employee.id, block_id)
    db.delete(block)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
