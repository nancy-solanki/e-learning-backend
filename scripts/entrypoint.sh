#!/usr/bin/env bash
# entrypoint.sh - Application entrypoint script for container execution

set -e

echo "=================================================="
echo "Starting E-Learning Backend Entrypoint..."
echo "=================================================="

# 1. Wait for Database
echo "[1/3] Waiting for database..."
bash ./scripts/wait_for_db.sh

# 2. Run Database Migrations
echo "[2/3] Applying database migrations..."
python manage.py migrate --noinput

# 3. Seed Database Data
if [ "${RUN_SEED_DATA:-true}" = "true" ]; then
    echo "[3/3] Running database seed script..."
    python scripts/seed_data.py
else
    echo "[3/3] Skipping seed data (RUN_SEED_DATA is set to false)."
fi

# Optional static file collection
if [ "${COLLECT_STATIC:-false}" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "=================================================="
echo "Initialization complete. Executing application command..."
echo "=================================================="

exec "$@"
