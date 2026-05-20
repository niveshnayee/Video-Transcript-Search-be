SHELL := /bin/bash

APP_IMAGE ?= video-app
PORT ?= 8000
REDIS_URL ?= redis://localhost:6379/0
DOCKER_REDIS_URL ?= redis://redis:6379/0
REDIS_CONTAINER ?= local-redis
CELERY_QUEUE ?= transcriptions
LOCAL_BIN_PATH := /opt/homebrew/bin:/usr/local/bin:$(PATH)
VENV := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest

.PHONY: help venv install build build-image docker-run compose-up compose-down test unit-test run local celery-worker redis-logs redis-monitor redis-queue celery-status dev all clean

help:
	@echo "Available make targets:"
	@echo "  make install       Create .venv and install Python dependencies with uv"
	@echo "  make build         Build the Docker image"
	@echo "  make test          Run unit tests"
	@echo "  make run           Run the FastAPI app locally"
	@echo "  make local         Install, test, start services, run app, then stop services on exit"
	@echo "  make celery-worker Run the Celery worker for background jobs"
	@echo "  make compose-up    Start Redis and MongoDB with Docker Compose"
	@echo "  make compose-down  Stop Docker Compose services"
	@echo "  make redis-logs    Follow Redis container logs"
	@echo "  make redis-monitor Watch Redis commands in real time"
	@echo "  make redis-queue   Show queued Celery jobs in Redis"
	@echo "  make celery-status Show Celery worker/queue status"
	@echo "  make docker-run    Build and run the app Docker container"
	@echo "  make dev           Start Redis/MongoDB and run the app locally; run worker separately"
	@echo "  make all           Install dependencies, run tests, and build image"

venv:
	@test -x $(PYTHON) || uv venv $(VENV)

install: venv
	uv pip install -r requirements.txt

build: build-image

build-image:
	docker build -t $(APP_IMAGE) .

docker-run: build-image
	docker run --rm -p $(PORT):$(PORT) --name $(APP_IMAGE) --link $(REDIS_CONTAINER):redis -e REDIS_URL=$(DOCKER_REDIS_URL) -e PORT=$(PORT) $(APP_IMAGE)

compose-up:
	docker compose up -d

compose-down:
	docker compose down

test unit-test: install
	PYTHONPATH=. $(PYTEST) -q

run: install
	PATH="$(LOCAL_BIN_PATH)" $(PYTHON) run.py

local: install test
	@set -e; \
	cleanup() { \
		echo ""; \
		echo "Stopping local Docker services..."; \
		$(MAKE) compose-down; \
	}; \
	trap cleanup EXIT; \
	$(MAKE) compose-up; \
	echo ""; \
	echo "Local API is starting on http://localhost:$(PORT)"; \
	echo "Background tasks need a worker. In another terminal, run: make celery-worker"; \
	echo ""; \
	PATH="$(LOCAL_BIN_PATH)" $(PYTHON) run.py

celery-worker: install
	PATH="$(LOCAL_BIN_PATH)" PYTHONPATH=. REDIS_URL=$(REDIS_URL) $(VENV)/bin/celery -A app.tasks.celery_worker.celery worker --loglevel=info -Q $(CELERY_QUEUE)

redis-logs:
	docker logs -f $(REDIS_CONTAINER)

redis-monitor:
	docker exec -it $(REDIS_CONTAINER) redis-cli MONITOR

redis-queue:
	docker exec -it $(REDIS_CONTAINER) redis-cli LLEN $(CELERY_QUEUE)

celery-status: install
	PATH="$(LOCAL_BIN_PATH)" PYTHONPATH=. REDIS_URL=$(REDIS_URL) $(VENV)/bin/celery -A app.tasks.celery_worker.celery inspect active
	PATH="$(LOCAL_BIN_PATH)" PYTHONPATH=. REDIS_URL=$(REDIS_URL) $(VENV)/bin/celery -A app.tasks.celery_worker.celery inspect reserved
	PATH="$(LOCAL_BIN_PATH)" PYTHONPATH=. REDIS_URL=$(REDIS_URL) $(VENV)/bin/celery -A app.tasks.celery_worker.celery inspect scheduled

dev: compose-up run

all: install test build

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
