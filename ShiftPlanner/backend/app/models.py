"""ORM-модели доменной области.

Домен: планирование рабочих смен в небольших компаниях (кафе, магазины).

Сущности и связи:
- User — учётная запись (роль manager или employee);
- Company — компания, создаётся менеджером, имеет код приглашения;
- Branch — филиал компании;
- Position — должность в компании;
- Employee — профиль сотрудника (связка User <-> Company);
- EmployeeAvailability — недельные интервалы, когда сотрудник может работать;
- Shift — конкретная смена: дата, время, филиал, должность, сотрудник.

Схема БД создаётся скриптом backend/db/schema.sql при первом старте
контейнера postgres; модели ниже должны ей соответствовать.
"""

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Учётная запись пользователя."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))  # 'manager' | 'employee'
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee_profile: Mapped["Employee | None"] = relationship(
        back_populates="user", uselist=False
    )


class Company(Base):
    """Компания. Создаётся менеджером; сотрудники вступают по коду приглашения."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    invite_code: Mapped[str] = mapped_column(String(16), unique=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    branches: Mapped[list["Branch"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    positions: Mapped[list["Position"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Branch(Base):
    """Филиал компании."""

    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company] = relationship(back_populates="branches")


class Position(Base):
    """Должность в компании (например, «Бариста», «Кассир»)."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))

    company: Mapped[Company] = relationship(back_populates="positions")


class Employee(Base):
    """Профиль сотрудника: привязка пользователя к компании, филиалу и должности."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"))
    position_id: Mapped[int | None] = mapped_column(ForeignKey("positions.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="employee_profile")
    company: Mapped[Company] = relationship(back_populates="employees")
    branch: Mapped["Branch | None"] = relationship()
    position: Mapped["Position | None"] = relationship()
    availability: Mapped[list["EmployeeAvailability"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )


class EmployeeAvailability(Base):
    """Интервал доступности сотрудника в недельном расписании.

    weekday: 0 — понедельник, 6 — воскресенье.
    """

    __tablename__ = "employee_availability"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "weekday", "start_time", "end_time",
            name="uq_availability_employee_weekday_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    employee: Mapped[Employee] = relationship(back_populates="availability")


class Shift(Base):
    """Смена: конкретный сотрудник в конкретные дату и время."""

    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"))
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id", ondelete="CASCADE"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    shift_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    branch: Mapped[Branch] = relationship()
    position: Mapped[Position] = relationship()
    employee: Mapped[Employee] = relationship()
