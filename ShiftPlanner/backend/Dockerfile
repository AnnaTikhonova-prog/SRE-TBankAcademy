# Образ бэкенда ShiftPlanner.
FROM python:3.12-slim

WORKDIR /app

# Сначала копируем только requirements.txt, чтобы слой с зависимостями
# кешировался Docker при изменении кода приложения.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Uvicorn корректно обрабатывает SIGTERM (фактор IX — утилизация).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
