FROM python:3.12-slim AS base

WORKDIR /app

RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
# backend/alembic and backend/alembic.ini are added once DB models land (IMPLEMENTATION_PLAN Phase 4)

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
