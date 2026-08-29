#!/bin/bash
set -e

# Run migrations
echo "Running Alembic migrations for ML Service..."
alembic upgrade head

# Run ML Training
echo "Running ML Training pipeline..."
export PYTHONPATH=/app
python training/train_demand_model.py

# Start application
echo "Starting ML Service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
