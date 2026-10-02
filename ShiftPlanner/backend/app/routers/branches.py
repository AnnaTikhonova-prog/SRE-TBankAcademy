"""Филиалы компании: CRUD-операции, доступные менеджеру."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_manager_company

router = APIRouter()


def _get_branch_or_404(db: Session, company_id: int, branch_id: int) -> models.Branch:
    """Ищет филиал внутри компании менеджера (чужие филиалы недоступны)."""
    branch = db.get(models.Branch, branch_id)
    if branch is None or branch.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Филиал не найден")
    return branch


@router.get("/", response_model=list[schemas.BranchRead])
def list_branches(company: models.Company = Depends(get_manager_company)):
    """Список филиалов компании."""
    return sorted(company.branches, key=lambda b: b.id)


@router.post("/", response_model=schemas.BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: schemas.BranchCreate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    branch = models.Branch(
        company_id=company.id, name=payload.name, address=payload.address
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.patch("/{branch_id}", response_model=schemas.BranchRead)
def update_branch(
    branch_id: int,
    payload: schemas.BranchUpdate,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    branch = _get_branch_or_404(db, company.id, branch_id)
    if payload.name is not None:
        branch.name = payload.name
    # null для address очищает адрес (учитываем только явно переданные поля).
    if "address" in payload.model_fields_set:
        branch.address = payload.address
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_manager_company),
):
    """Удаление филиала. Его смены удаляются каскадно, у сотрудников
    поле branch_id обнуляется (ON DELETE SET NULL в схеме БД)."""
    branch = _get_branch_or_404(db, company.id, branch_id)
    db.delete(branch)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
