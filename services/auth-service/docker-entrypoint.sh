#!/bin/bash
set -e

# Run migrations
echo "Running Alembic migrations for Auth Service..."
alembic upgrade head

# Start application
echo "Starting Auth Service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
