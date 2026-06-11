#!/usr/bin/env bash
set -e

ROLE="${1:-api}"

case "$ROLE" in
  api)
    echo "Running database migrations..."
    alembic upgrade head
    echo "Starting API server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
    ;;
  worker)
    echo "Starting Celery worker (with embedded beat scheduler)..."
    exec celery -A app.workers.celery_app.celery_app worker --beat --loglevel=info --concurrency=4
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  *)
    exec "$@"
    ;;
esac
