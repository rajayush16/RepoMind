FROM python:3.12-slim AS base

WORKDIR /app

# git is required at runtime: the indexing pipeline shells out to it to clone
# repositories and list tracked (non-.gitignored) files.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

USER appuser

CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info"]
