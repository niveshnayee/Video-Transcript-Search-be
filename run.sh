#!/bin/bash

# File: run.sh (place this in your project root)
# Usage: 
# 1. Make it executable: chmod +x run.sh
# 2. Run it: ./run.sh

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Start Redis in the background
redis-server --daemonize yes

# Start Celery worker for the "transcriptions" queue
celery -A app.tasks.celery_worker worker --loglevel=info -Q transcriptions --pool=solo &

# Start Flower for monitoring (port 5555)
celery -A app.tasks.celery_worker flower --port=5555 &

# Start FastAPI backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000