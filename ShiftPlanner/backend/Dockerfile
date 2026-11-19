# Образ бэкенда ShiftPlanner.
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

ARG APP_VERSION=1.0.0
ARG APP_RELEASE=stable
ENV APP_VERSION=${APP_VERSION} \
    APP_RELEASE=${APP_RELEASE}

WORKDIR /app

# Сначала копируем только requirements.txt, чтобы слой с зависимостями
# кешировался Docker при изменении кода приложения.
COPY requirements.txt .
COPY psycopg_binary-3.2.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl /tmp/psycopg_binary-3.2.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
# Verify the PyPI-published hash; Docker Desktop's network returned a corrupt
# copy of this wheel, so install the verified local copy before resolving extras.
RUN echo "64a607e630d9f4b2797f641884e52b9f8e239d35943f51bef817a384ec1678fe  /tmp/psycopg_binary-3.2.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl" | sha256sum -c - \
    && pip install --no-cache-dir /tmp/psycopg_binary-3.2.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl \
    && pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY app ./app
COPY logging.json ./logging.json

EXPOSE 8000

# Uvicorn корректно обрабатывает SIGTERM (фактор IX — утилизация).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "/app/logging.json"]
