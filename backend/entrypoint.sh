#!/bin/sh
set -e

python entrypoint.py

PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
exec gunicorn app.main:app --workers "$WORKERS" \
  --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$PORT"
