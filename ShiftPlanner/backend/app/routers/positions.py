"""Должности компании: CRUD-операции, доступные менеджеру."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_manager_company

router = APIRouter()


def _get_position_or_404(db: Session, company_id: int, position_id: int) -> models.Position:
    position = db.get(models.Position, position_id)
    if position is None or position.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Должность не найдена")
    return position


@router.get("/", response_model=list[schemas.PositionRead])
def list_positions(company: models.Company = Depends(get_manager_company)):
    return sorted(company.positions, key=lambda p: p.id)


@router.post("/", response_model=schemas.PositionRead, status_code=status.HTTP_201_CREATED)
def create_position(
    payload: schemas.PositionCreate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    position = models.Position(company_id=company.id, name=payload.name)
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


@router.patch("/{position_id}", response_model=schemas.PositionRead)
def update_position(
    position_id: int,
    payload: schemas.PositionUpdate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    position = _get_position_or_404(db, company.id, position_id)
    if payload.name is not None:
        position.name = payload.name
    db.commit()
    db.refresh(position)
    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    position = _get_position_or_404(db, company.id, position_id)
    db.delete(position)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
