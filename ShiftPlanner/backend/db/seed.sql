-- Демонстрационные данные ShiftPlanner (учебная версия).
-- Применяется после schema.sql при первом старте контейнера postgres.
--
-- Учётные записи (пароль -> bcrypt-хеш):
--   manager@example.com  / manager123   (менеджер)
--   ivan@example.com     / employee123  (сотрудник)
--   anna@example.com     / employee123  (сотрудник)

INSERT INTO users (full_name, email, password_hash, role) VALUES
('Мария Менеджер', 'manager@example.com',
 '$2b$12$oo5ryRPAlz/TOfenPoE3JuFYJsdljzAhv.FLXcvx6vrvCPcCA1kTm', 'manager'),
('Иван Бариста', 'ivan@example.com',
 '$2b$12$uSYcqEdeSEBbX1C4vnns9.33t2QvChgi0eQ5RxJBGg8jCHGqu3w8a', 'employee'),
('Анна Кассир', 'anna@example.com',
 '$2b$12$uSYcqEdeSEBbX1C4vnns9.33t2QvChgi0eQ5RxJBGg8jCHGqu3w8a', 'employee');

INSERT INTO companies (name, address, invite_code, manager_id) VALUES
('Кофейня «Уютная»', 'г. Москва, ул. Примерная, 1', 'COFFEE42', 1);

INSERT INTO branches (company_id, name, address) VALUES
(1, 'Центральный', 'г. Москва, ул. Примерная, 1'),
(1, 'Набережная', 'г. Москва, наб. Речная, 12');

INSERT INTO positions (company_id, name) VALUES
(1, 'Бариста'),
(1, 'Кассир');

INSERT INTO employees (user_id, company_id, branch_id, position_id) VALUES
(2, 1, 1, 1),
(3, 1, 2, 2);

-- Недельная доступность сотрудников (weekday: 0 — понедельник, 6 — воскресенье).
INSERT INTO employee_availability (employee_id, weekday, start_time, end_time) VALUES
(1, 0, '09:00', '18:00'),
(1, 1, '09:00', '18:00'),
(1, 2, '09:00', '18:00'),
(1, 3, '09:00', '18:00'),
(1, 4, '09:00', '15:00'),
(2, 2, '12:00', '21:00'),
(2, 3, '12:00', '21:00'),
(2, 4, '12:00', '21:00'),
(2, 5, '10:00', '20:00'),
(2, 6, '10:00', '20:00');

-- Смены на текущую неделю (даты считаются от дня первого запуска БД).
INSERT INTO shifts (company_id, branch_id, position_id, employee_id, shift_date, start_time, end_time) VALUES
(1, 1, 1, 1, CURRENT_DATE,     '09:00', '17:00'),
(1, 1, 1, 1, CURRENT_DATE + 1, '09:00', '17:00'),
(1, 2, 2, 2, CURRENT_DATE,     '12:00', '20:00'),
(1, 2, 2, 2, CURRENT_DATE + 2, '12:00', '20:00'),
(1, 1, 1, 1, CURRENT_DATE + 3, '09:00', '15:00');
