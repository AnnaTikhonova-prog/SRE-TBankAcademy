-- Схема базы данных ShiftPlanner (учебная версия).
-- Применяется автоматически при первом старте контейнера postgres
-- (скрипты из /docker-entrypoint-initdb.d выполняются на пустом volume).

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    full_name     VARCHAR(255) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          VARCHAR(20) NOT NULL CHECK (role IN ('manager', 'employee')),
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE companies (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    address     TEXT,
    invite_code VARCHAR(16) UNIQUE NOT NULL,
    manager_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE branches (
    id         SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name       VARCHAR(255) NOT NULL,
    address    TEXT
);

CREATE TABLE positions (
    id         SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL
);

CREATE TABLE employees (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    company_id  INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    branch_id   INTEGER REFERENCES branches(id) ON DELETE SET NULL,
    position_id INTEGER REFERENCES positions(id) ON DELETE SET NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE employee_availability (
    id          SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    weekday     INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL,
    CHECK (end_time > start_time),
    CONSTRAINT uq_availability_employee_weekday_time
        UNIQUE (employee_id, weekday, start_time, end_time)
);

CREATE TABLE shifts (
    id          SERIAL PRIMARY KEY,
    company_id  INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    branch_id   INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    position_id INTEGER NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    shift_date  DATE NOT NULL,
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    CHECK (end_time > start_time)
);

-- Индексы под типовые запросы: смены компании за период и смены сотрудника.
CREATE INDEX idx_shifts_company_date ON shifts (company_id, shift_date);
CREATE INDEX idx_shifts_employee_date ON shifts (employee_id, shift_date);
CREATE INDEX idx_employees_company ON employees (company_id);
