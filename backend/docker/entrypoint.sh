#!/bin/bash
# Entrypoint del contenedor Docker.
# Acepta: api | worker | flower

set -euo pipefail

COMMAND="${1:-api}"

echo "=== Flamenco2Techno AI ==="
echo "Command: $COMMAND"
echo "Python: $(python --version)"
echo "FFmpeg: $(ffmpeg -version 2>&1 | head -1)"

case "$COMMAND" in
  api)
    echo "Starting FastAPI with Uvicorn..."
    exec uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --workers 2 \
      --loop uvloop \
      --http httptools \
      --log-level info \
      --access-log
    ;;

  worker)
    echo "Starting Celery worker..."
    exec celery -A app.core.celery_app.celery_app worker \
      --loglevel=info \
      --queues=conversion,analysis \
      --concurrency=1 \
      --max-tasks-per-child=10 \
      --hostname="worker@%h"
    ;;

  flower)
    echo "Starting Flower monitoring..."
    exec celery -A app.core.celery_app.celery_app flower \
      --port=5555 \
      --broker="${REDIS_URL}"
    ;;

  *)
    echo "Unknown command: $COMMAND"
    echo "Available: api | worker | flower"
    exit 1
    ;;
esac
