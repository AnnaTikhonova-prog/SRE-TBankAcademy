# ShiftPlanner (учебная версия)

Клиент-серверное приложение для планирования рабочих смен в небольших
компаниях (кафе, магазины, сервисные точки).

Упрощённая версия командного проекта
[ShiftPlanner](https://github.com/shift-happens-daily/ShiftPlanner),
адаптированная для учебных целей: убраны авто-генератор расписаний на
OR-Tools, email-уведомления, импорт из Excel и мобильные клиенты;
оставлены JWT-авторизация и CRUD-операции над основными сущностями.

## Стек

- **Бэкенд:** Python 3.12, FastAPI, SQLAlchemy 2, JWT (python-jose), bcrypt
- **Фронтенд:** React 18, Vite, axios
- **БД:** PostgreSQL 16
- **Инфраструктура:** Docker, docker-compose, nginx (раздача статики и прокси /api)

## Возможности

- Регистрация и вход по JWT (роли: менеджер / сотрудник);
- Менеджер: создаёт компанию, получает код приглашения, управляет
  филиалами, должностями, сотрудниками и сменами (полный CRUD);
- Сотрудник: вступает в компанию по коду приглашения, указывает свою
  недельную доступность, смотрит свои смены;
- Бэкенд не даёт назначить сотруднику пересекающиеся смены.

## Быстрый старт (Docker)

Требования: Docker Desktop с docker-compose.

```bash
cp .env.example .env        # при желании поменяйте JWT_SECRET_KEY и пароли
docker compose up --build
```

После запуска:

| Адрес | Что это |
|---|---|
| http://localhost:8080 | Веб-приложение |
| http://localhost:8000/docs | Swagger UI (документация API) |
| http://localhost:8000/health | Проверка живости бэкенда |
| http://localhost:8000/health/db | Проверка соединения с БД |

Демо-аккаунты (создаются скриптом `backend/db/seed.sql`):

| Роль | Email | Пароль |
|---|---|---|
| Менеджер | `manager@example.com` | `manager123` |
| Сотрудник | `ivan@example.com` | `employee123` |
| Сотрудник | `anna@example.com` | `employee123` |

Код приглашения демо-компании «Кофейня „Уютная“»: **COFFEE42**.

Остановить стек: `docker compose down`.
Пересоздать БД с нуля: `docker compose down -v && docker compose up --build`
(флаг `-v` удаляет volume с данными, схема и демо-данные применятся заново).

## Локальный запуск без Docker (для разработки)

Нужен локальный PostgreSQL с базой из `backend/db/schema.sql` и `seed.sql`.

```bash
# Бэкенд (http://localhost:8000)
cd backend
cp .env.example .env
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Фронтенд (http://localhost:5173, /api проксируется на :8000)
cd frontend
cp .env.example .env
npm ci
npm run dev
```

## Структура проекта

```text
ShiftPlanner/
├── backend/
│   ├── app/
│   │   ├── main.py          # сборка FastAPI-приложения, health-эндпоинты
│   │   ├── config.py        # настройки из переменных окружения
│   │   ├── database.py      # подключение к PostgreSQL
│   │   ├── models.py        # ORM-модели (User, Company, Branch, ...)
│   │   ├── schemas.py       # Pydantic-схемы запросов/ответов
│   │   ├── security.py      # bcrypt-хеширование и JWT
│   │   ├── deps.py          # зависимости: текущий пользователь, роли
│   │   └── routers/         # auth, companies, branches, positions,
│   │                        # employees, availability, shifts
│   ├── db/
│   │   ├── schema.sql       # схема БД (применяется при первом старте)
│   │   └── seed.sql         # демо-данные
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.js           # axios-клиент с JWT-перехватчиком
│   │   ├── auth.jsx         # контекст авторизации
│   │   ├── App.jsx          # выбор экрана по роли
│   │   ├── pages/           # AuthPage, ManagerPage, EmployeePage
│   │   └── components/      # Layout и вкладки с CRUD-таблицами
│   ├── Dockerfile           # сборка Vite + раздача через nginx
│   └── nginx.conf           # статика + прокси /api -> backend
├── scripts/
│   └── smoke_test.py      # end-to-end проверка API против живого сервера
├── docker-compose.yml
├── .env.example
└── Отчёт.md
```

## Проверка API без браузера

Скрипт `scripts/smoke_test.py` прогоняет сквозной сценарий (регистрация,
создание компании, CRUD филиалов/должностей/смен, права доступа)
против запущенного стека:

```bash
python scripts/smoke_test.py http://localhost:8000
# ожидаемый финал: "Итог: 44 passed, 0 failed"
```

## API (кратко)

| Метод | Путь | Кто | Описание |
|---|---|---|---|
| POST | `/auth/register` | все | регистрация |
| POST | `/auth/login` | все | вход, выдача JWT |
| GET | `/auth/me` | авторизован | профиль текущего пользователя |
| POST | `/companies/` | менеджер | создать компанию |
| GET/PATCH | `/companies/my` | менеджер/сотрудник | своя компания |
| POST | `/companies/join` | сотрудник | вступить по коду приглашения |
| GET/POST | `/branches/` | менеджер | список/создание филиалов |
| PATCH/DELETE | `/branches/{id}` | менеджер | изменение/удаление филиала |
| GET/POST | `/positions/` | менеджер | список/создание должностей |
| PATCH/DELETE | `/positions/{id}` | менеджер | изменение/удаление должности |
| GET | `/employees/` | менеджер | список сотрудников |
| GET/PATCH/DELETE | `/employees/{id}` | менеджер | карточка/изменение/удаление |
| GET | `/employees/{id}/availability` | менеджер | доступность сотрудника |
| GET | `/availability/my` | сотрудник | своя доступность |
| POST/PATCH/DELETE | `/availability/...` | сотрудник | управление доступностью |
| GET | `/shifts/?date_from=&date_to=` | все | смены (менеджер — все, сотрудник — свои) |
| POST/PATCH/DELETE | `/shifts/...` | менеджер | управление сменами |
