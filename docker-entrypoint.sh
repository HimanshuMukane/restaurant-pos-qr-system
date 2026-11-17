#!/bin/sh
set -e

# On first boot (or after a rebuild), seed demo data if the DB is empty
if [ "$DEMO_MODE" = "1" ]; then
  echo "[demo] Checking for seed data..."
  python scripts/demo_seed.py --if-empty
fi

exec gunicorn \
  --worker-class eventlet \
  -w 1 \
  --bind "0.0.0.0:${PORT:-8080}" \
  --timeout 120 \
  wsgi:app
