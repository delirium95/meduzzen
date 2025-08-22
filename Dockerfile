# Backend Dockerfile
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (mostly optional since we use psycopg[binary])
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App code
COPY . /app

EXPOSE 8000

# DATABASE_URL should be provided at runtime, compose sets it
ENV DATABASE_URL="postgresql://postgres:root@db:5432/meduzzen_db"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app", "--reload-exclude", "frontend"]


