"""Pydantic-схемы запросов и ответов REST API.

Отделяют транспортное представление от ORM-моделей: наружу не утекают
хеши паролей и внутренние поля, а входные данные валидируются автоматически.
"""

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Role = Literal["manager", "employee"]


# ---------------------------------------------------------------------------
# Аутентификация
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    # bcrypt работает максимум с 72 байтами пароля — ограничиваем явно.
    password: str = Field(min_length=8, max_length=72)
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class EmployeeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int | None
    position_id: int | None
    is_active: bool


class CompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str | None
    invite_code: str


class UserRead(BaseModel):
    """Профиль текущего пользователя (ответ /auth/me и /auth/register)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: Role
    company: CompanyBrief | None = None
    employee: EmployeeBrief | None = None


# ---------------------------------------------------------------------------
# Компании
# ---------------------------------------------------------------------------

class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str | None
    invite_code: str


class JoinCompanyRequest(BaseModel):
    invite_code: str = Field(min_length=1, max_length=16)


# ---------------------------------------------------------------------------
# Филиалы и должности
# ---------------------------------------------------------------------------

class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str | None


class PositionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PositionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class PositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# ---------------------------------------------------------------------------
# Сотрудники
# ---------------------------------------------------------------------------

class EmployeeUpdate(BaseModel):
    """Что менеджер может изменить в профиле сотрудника."""

    branch_id: int | None = None
    position_id: int | None = None
    is_active: bool | None = None


class EmployeeRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    branch_id: int | None
    branch_name: str | None
    position_id: int | None
    position_name: str | None
    is_active: bool


# ---------------------------------------------------------------------------
# Доступность сотрудника
# ---------------------------------------------------------------------------

class AvailabilityBase(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0 — понедельник, 6 — воскресенье")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time должен быть позже start_time")
        return self


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityUpdate(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None


class AvailabilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    weekday: int
    start_time: time
    end_time: time


# ---------------------------------------------------------------------------
# Смены
# ---------------------------------------------------------------------------

class ShiftBase(BaseModel):
    branch_id: int
    position_id: int
    employee_id: int
    shift_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time должен быть позже start_time")
        return self


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    branch_id: int | None = None
    position_id: int | None = None
    employee_id: int | None = None
    shift_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None


class ShiftRead(BaseModel):
    id: int
    shift_date: date
    start_time: time
    end_time: time
    branch_id: int
    branch_name: str
    position_id: int
    position_name: str
    employee_id: int
    employee_name: str
