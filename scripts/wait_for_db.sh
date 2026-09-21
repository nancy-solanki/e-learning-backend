#!/usr/bin/env bash
# wait_for_db.sh - Wait for database connection before proceeding

set -e

HOST="${DB_HOST:-localhost}"
PORT="${DB_PORT:-5432}"
MAX_RETRIES="${DB_WAIT_RETRIES:-30}"
SLEEP_INTERVAL="${DB_WAIT_INTERVAL:-1}"

echo "=================================================="
echo "Checking database connection..."
echo "=================================================="

retries=0
until python -c "
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.development'))
django.setup()

from django.db import connection

try:
    connection.ensure_connection()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  retries=$((retries + 1))
  if [ "$retries" -ge "$MAX_RETRIES" ]; then
    echo "ERROR: Database unavailable after $MAX_RETRIES attempts. Exiting."
    exit 1
  fi
  echo "Database unavailable at ${HOST}:${PORT} (attempt $retries/$MAX_RETRIES) - waiting ${SLEEP_INTERVAL}s..."
  sleep "$SLEEP_INTERVAL"
done

echo "Database is ready and accepting connections!"
