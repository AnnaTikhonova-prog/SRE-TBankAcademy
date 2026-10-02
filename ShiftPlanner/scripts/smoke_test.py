"""End-to-end smoke-тест API ShiftPlanner против живого сервера.

Прогоняет основной пользовательский сценарий:
здоровье -> регистрация -> создание компании -> CRUD филиалов/должностей ->
вступление сотрудника -> доступность -> смены (включая проверку пересечений)
-> проверки прав доступа.

Запуск: python _smoke_test.py [BASE_URL]   (по умолчанию http://127.0.0.1:8000)
"""

import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

passed = 0
failed = 0


def req(method, path, body=None, token=None):
    """Выполняет HTTP-запрос и возвращает (status, json|None)."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  OK   {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


print(f"== Smoke-тест API: {BASE} ==")

# --- health ---
s, _ = req("GET", "/health")
check("GET /health -> 200", s == 200)
s, b = req("GET", "/health/db")
check("GET /health/db -> 200 ok", s == 200 and b.get("status") == "ok", f"({s}, {b})")

# --- демо-аккаунт из seed.sql ---
s, b = req("POST", "/auth/login", {"email": "manager@example.com", "password": "manager123"})
check("login демо-менеджера", s == 200 and b.get("access_token"), f"({s})")
demo_mgr = b["access_token"] if s == 200 else None
s, b = req("GET", "/companies/my", token=demo_mgr)
check("у демо-менеджера есть компания из seed", s == 200 and b.get("invite_code") == "COFFEE42", f"({s}, {b})")
s, b = req("GET", "/shifts/", token=demo_mgr)
check("у демо-компании есть смены из seed", s == 200 and len(b) >= 1, f"({s}, n={len(b) if isinstance(b, list) else '?'})")
s, b = req("POST", "/auth/login", {"email": "ivan@example.com", "password": "employee123"})
check("login демо-сотрудника", s == 200 and b.get("access_token"), f"({s})")
demo_emp = b["access_token"] if s == 200 else None
s, b = req("GET", "/shifts/", token=demo_emp)
check("демо-сотрудник видит только свои смены", s == 200 and all(x["employee_name"] == "Иван Бариста" for x in b), f"({s})")

# --- регистрация нового менеджера и полный CRUD-цикл ---
suffix = uuid.uuid4().hex[:8]
mgr_email = f"mgr_{suffix}@test.dev"
s, b = req("POST", "/auth/register", {"full_name": "Тест Менеджер", "email": mgr_email, "password": "password123", "role": "manager"})
check("register manager -> 201", s == 201 and b["role"] == "manager", f"({s}, {b})")
s, b = req("POST", "/auth/login", {"email": mgr_email, "password": "password123"})
check("login manager -> token", s == 200 and b.get("access_token"), f"({s})")
mgr = b["access_token"]

s, b = req("POST", "/companies/", {"name": "Тест-Кафе", "address": "ул. Тестовая, 1"}, token=mgr)
check("create company -> 201 + invite_code", s == 201 and len(b.get("invite_code", "")) == 8, f"({s}, {b})")
invite = b["invite_code"] if s == 201 else None
s, b = req("POST", "/companies/", {"name": "Вторая"}, token=mgr)
check("вторая компания -> 409", s == 409, f"({s})")
s, b = req("PATCH", "/companies/my", {"address": "ул. Новая, 2"}, token=mgr)
check("patch company -> 200", s == 200 and b["address"] == "ул. Новая, 2", f"({s})")

# филиалы: CRUD
s, b = req("POST", "/branches/", {"name": "Филиал 1", "address": "Адрес 1"}, token=mgr)
check("create branch -> 201", s == 201, f"({s})")
branch_id = b["id"] if s == 201 else None
s, b = req("PATCH", f"/branches/{branch_id}", {"name": "Филиал 1*"}, token=mgr)
check("patch branch -> 200", s == 200 and b["name"] == "Филиал 1*", f"({s})")
s, b = req("GET", "/branches/", token=mgr)
check("list branches -> 1", s == 200 and len(b) == 1, f"({s}, {b})")

# должности: CRUD
s, b = req("POST", "/positions/", {"name": "Бариста"}, token=mgr)
check("create position -> 201", s == 201, f"({s})")
pos_id = b["id"] if s == 201 else None
s, b = req("PATCH", f"/positions/{pos_id}", {"name": "Старший бариста"}, token=mgr)
check("patch position -> 200", s == 200 and b["name"] == "Старший бариста", f"({s})")

# сотрудник: регистрация и вступление
emp_email = f"emp_{suffix}@test.dev"
s, b = req("POST", "/auth/register", {"full_name": "Тест Сотрудник", "email": emp_email, "password": "password123", "role": "employee"})
check("register employee -> 201", s == 201, f"({s})")
s, b = req("POST", "/auth/login", {"email": emp_email, "password": "password123"})
emp = b["access_token"]

s, b = req("POST", "/companies/join", {"invite_code": "WRONG99"}, token=emp)
check("join с неверным кодом -> 404", s == 404, f"({s})")
s, b = req("POST", "/companies/join", {"invite_code": invite}, token=emp)
check("join по коду -> 201", s == 201, f"({s}, {b})")
emp_id = b["id"] if s == 201 else None

# доступность сотрудника
s, b = req("POST", "/availability/", {"weekday": 0, "start_time": "09:00", "end_time": "18:00"}, token=emp)
check("create availability -> 201", s == 201, f"({s}, {b})")
av_id = b["id"] if s == 201 else None
s, b = req("POST", "/availability/", {"weekday": 0, "start_time": "18:00", "end_time": "09:00"}, token=emp)
check("availability end<start -> 422", s == 422, f"({s})")
s, b = req("GET", "/availability/my", token=emp)
check("list my availability -> 1", s == 200 and len(b) == 1, f"({s})")

# менеджер видит сотрудника и его доступность, назначает филиал/должность
s, b = req("GET", "/employees/", token=mgr)
check("manager видит сотрудника", s == 200 and any(e["id"] == emp_id for e in b), f"({s})")
s, b = req("PATCH", f"/employees/{emp_id}", {"branch_id": branch_id, "position_id": pos_id}, token=mgr)
check("manager назначает филиал/должность", s == 200 and b["branch_id"] == branch_id, f"({s}, {b})")
s, b = req("PATCH", f"/employees/{emp_id}", {"branch_id": None}, token=mgr)
check("сброс филиала через null", s == 200 and b["branch_id"] is None, f"({s}, {b})")
s, b = req("PATCH", f"/employees/{emp_id}", {"branch_id": branch_id}, token=mgr)
check("повторное назначение филиала", s == 200 and b["branch_id"] == branch_id, f"({s}, {b})")
s, b = req("GET", f"/employees/{emp_id}/availability", token=mgr)
check("manager видит доступность сотрудника", s == 200 and len(b) == 1, f"({s})")

# смены: создание, пересечение, правка, удаление
s, b = req("POST", "/shifts/", {"branch_id": branch_id, "position_id": pos_id, "employee_id": emp_id,
                                "shift_date": "2030-01-06", "start_time": "10:00", "end_time": "18:00"}, token=mgr)
check("create shift -> 201", s == 201, f"({s}, {b})")
shift_id = b["id"] if s == 201 else None
s, b = req("POST", "/shifts/", {"branch_id": branch_id, "position_id": pos_id, "employee_id": emp_id,
                                "shift_date": "2030-01-06", "start_time": "12:00", "end_time": "20:00"}, token=mgr)
check("пересекающаяся смена -> 409", s == 409, f"({s}, {b})")
s, b = req("POST", "/shifts/", {"branch_id": branch_id, "position_id": pos_id, "employee_id": emp_id,
                                "shift_date": "2030-01-06", "start_time": "18:00", "end_time": "22:00"}, token=mgr)
check("соседняя смена (стык в стык) -> 201", s == 201, f"({s})")
shift2_id = b["id"] if s == 201 else None
s, b = req("PATCH", f"/shifts/{shift_id}", {"end_time": "17:30"}, token=mgr)
check("patch shift -> 200", s == 200 and b["end_time"].startswith("17:30"), f"({s}, {b})")
s, b = req("PATCH", f"/shifts/{shift_id}", {"end_time": "19:00"}, token=mgr)
check("patch shift с пересечением -> 409", s == 409, f"({s}, {b})")
s, b = req("GET", "/shifts/?date_from=2030-01-01&date_to=2030-01-31", token=mgr)
check("manager list shifts за январь 2030 -> 2", s == 200 and len(b) == 2, f"({s}, n={len(b) if isinstance(b, list) else '?'})")
s, b = req("GET", "/shifts/", token=emp)
check("employee видит свои смены", s == 200 and all(x["employee_id"] == emp_id for x in b), f"({s})")
s, b = req("DELETE", f"/shifts/{shift2_id}", token=mgr)
check("delete shift -> 204", s == 204, f"({s})")

# права доступа
s, b = req("POST", "/branches/", {"name": "Хак"}, token=emp)
check("employee не может создать филиал -> 403", s == 403, f"({s})")
s, b = req("GET", "/employees/", token=emp)
check("employee не может видеть список сотрудников -> 403", s == 403, f"({s})")
s, b = req("GET", "/shifts/")
check("без токена -> 401", s == 401, f"({s})")
s, b = req("GET", "/shifts/", token="bad.token.here")
check("битый токен -> 401", s == 401, f"({s})")

# удаление сущностей
s, b = req("DELETE", f"/availability/{av_id}", token=emp)
check("delete availability -> 204", s == 204, f"({s})")
s, b = req("DELETE", f"/employees/{emp_id}", token=mgr)
check("delete employee -> 204", s == 204, f"({s})")
s, b = req("DELETE", f"/positions/{pos_id}", token=mgr)
check("delete position -> 204", s == 204, f"({s})")
s, b = req("DELETE", f"/branches/{branch_id}", token=mgr)
check("delete branch -> 204", s == 204, f"({s})")

print(f"== Итог: {passed} passed, {failed} failed ==")
sys.exit(1 if failed else 0)
