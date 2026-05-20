# Smart Video Search

This project is built with **FastAPI** and provides a unified upload path for both Cloudflare R2 video uploads and YouTube URLs. It uses **MongoDB** to store metadata, **Celery** for asynchronous processing, and **Cloudflare R2** for video storage.

---

## Features

- **Unified upload endpoint** for R2 and YouTube.
- **Presigned R2 uploads** with file validation before URL generation.
- **Asynchronous processing** using Celery and Redis.
- **Transcript search** with both basic and semantic strategies.
- **MongoDB storage** for video metadata, status and transcripts.
- **Modular, maintainable code** with separate routers, services, and utils.

---

## Project Structure

```
.
├── app/
│   ├── config/                    # Application and R2 configuration
│   ├── constants.py               # Shared constants and enums
│   ├── exceptions.py              # Custom exceptions
│   ├── logging_config.py          # Logging setup
│   ├── main.py                    # FastAPI entry point
│   ├── dependencies.py            # Dependency injection helpers
│   ├── routers/                   # API route modules
│   │   ├── video.py               # Unified upload and video metadata/search APIs
│   │   └── r2.py                  # R2 presign and delete APIs
│   ├── services/                  # Business and processing logic
│   │   ├── storage/               # Cloudflare R2 storage service
│   │   ├── transcription/         # Whisper transcription service
│   │   ├── search/                # Search strategies
│   │   └── video/                 # Video processing orchestration
│   ├── tasks/                     # Celery worker and task config
│   ├── utils/                     # Utility helpers
│   ├── mongoDb/                   # MongoDB connection and repository
│   └── schemas/                   # Pydantic models
├── docs/                          # Documentation assets
│   └── Complete_Flow_Diagram.md   # Current flow diagram
├── run.py                         # Start FastAPI server
├── Makefile                       # Local build, test, and run commands
├── docker-compose.yml             # Local Redis and MongoDB services
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
```

---

## Installation

### Prerequisites

- Python 3.10+
- ffmpeg
- Redis
- MongoDB
- Cloudflare R2 bucket and credentials

### Steps

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2. Create and activate a Python virtual environment (recommended):
  ```bash
  uv venv .venv
  # macOS / Linux
  source .venv/bin/activate
  # Windows (PowerShell)
  .\.venv\Scripts\Activate.ps1
  ```

3. Install dependencies inside the virtual environment:
  ```bash
  uv pip install -r requirements.txt
  ```

   Audio extraction uses `ffmpeg`. On macOS, install it with:

  ```bash
  brew install ffmpeg
  ```

  If the Celery worker still cannot find ffmpeg after installation, restart the worker or set the binary path explicitly:

  ```bash
  FFMPEG_BINARY=/opt/homebrew/bin/ffmpeg make celery-worker
  ```

4. Create a `.env` file in the project root:
    ```env
    MONGO_USERNAME=<your-mongo-username>
    MONGO_PASSWORD=<your-mongo-password>
    DATABASE_NAME=<your-database-name>
    MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>/<database>?retryWrites=true&w=majority
    R2_ACCOUNT_ID=<your-r2-account-id>
    R2_ACCESS_KEY_ID=<your-r2-access-key-id>
    R2_SECRET_ACCESS_KEY=<your-r2-secret-access-key>
    R2_BUCKET_NAME=<your-r2-bucket-name>
    REDIS_URL=redis://localhost:6379/0
    HOST=0.0.0.0
    PORT=8000
    RELOAD=true
    ALLOWED_ORIGINS=http://localhost:4200
    LOG_LEVEL=INFO
    ```

---

## API Endpoints

### Upload

- `POST /api/upload`
  - Unified upload endpoint.
  - Accepts either:
    - `url` for YouTube video metadata registration.
    - `file_id` for a previously uploaded R2 object.
  - Optional `submission_id` can be provided by the client. If omitted, the API generates one.
  - `submission_id` is stored in MongoDB with a unique index, so duplicate submissions are rejected.
  - Optional metadata: `name`, `category`, `description`.
  - Returns `video_id`, `submission_id`, `task_id`, and queues background processing.

### R2 Upload Support

- `POST /api/r2/presign`
  - Request: `file_name`, `file_size`
  - Returns: `upload_url`, `file_id`
- `DELETE /api/r2/files/{file_id}`
  - Deletes the object from Cloudflare R2.

### Video Management

- `GET /api/videos`
  - Retrieve all video metadata.
- `GET /api/video/{video_id}`
  - Retrieve details for a single video.
- `DELETE /api/video/{video_id}`
  - Delete video metadata and cleanup R2 storage if applicable.

### Transcript Search

- `POST /api/video/{video_id}/search`
  - Search the selected video transcript.

### Background Task Status

- `GET /api/task/{task_id}`
  - Check a Celery background task by the `task_id` returned from `POST /api/upload`.
  - Returns the current Celery status, such as `PENDING`, `STARTED`, `SUCCESS`, or `FAILURE`.

---

## Background Processing

- Background task: `app.services.video.video_processing.process_video_background_task`
- The task is queued after upload registration.
- The upload response includes `task_id` and `queue` so you can inspect the background job.
- Processing logic:
  - `r2`: download the file from R2 and transcribe.
  - `youtube`: download from YouTube, update metadata, and transcribe.
- Transcript data is saved in MongoDB and the video status is updated.

---

## Notes

- The upload model is flexible: only one of `url` or `file_id` is required.
- R2 presign validation verifies file extension and file size before returning a URL.
- The upload route is lightweight and delegates heavy work to Celery workers.
- The code is designed to be modular and maintainable, with separate routers and services.

---

## Makefile Commands

The `Makefile` gives you short commands for common local development tasks. Run these commands from the project root.

To see all available commands:

```bash
make help
```

### Command Reference

| Command | What it does |
| --- | --- |
| `make install` | Creates `.venv` if it does not exist, then installs packages from `requirements.txt` with `uv pip install`. |
| `make build` | Builds the Docker image using the local `Dockerfile`. The default image name is `video-app`. |
| `make test` | Runs `make install` first, then runs unit tests with `pytest`. |
| `make unit-test` | Same as `make test`. |
| `make run` | Runs `make install` first, then starts the FastAPI app locally with `python run.py`. |
| `make local` | Runs install, unit tests, starts Redis and MongoDB, runs the API, and automatically stops Docker services when the API exits or you press Ctrl-C. |
| `make celery-worker` | Runs the Celery worker that consumes background video processing jobs from the `transcriptions` queue. |
| `make compose-up` | Starts Redis and MongoDB in the background using `docker-compose.yml`. |
| `make compose-down` | Stops and removes the Redis and MongoDB containers created by Docker Compose. |
| `make redis-logs` | Follows the Redis Docker container logs. |
| `make redis-monitor` | Opens `redis-cli MONITOR` so you can see Redis commands in real time. |
| `make redis-queue` | Shows how many Celery jobs are waiting in the `transcriptions` Redis queue. |
| `make celery-status` | Shows active, reserved, and scheduled Celery tasks known to the worker. |
| `make docker-run` | Builds the Docker image, then runs the app container and exposes it on the configured port. |
| `make dev` | Starts Redis and MongoDB with Docker Compose, then runs the FastAPI app locally. Run `make celery-worker` separately for background jobs. |
| `make all` | Runs install, unit tests, and Docker image build in order. |
| `make clean` | Removes Python `__pycache__` folders from the project. |

### Common Examples

Install dependencies:

```bash
make install
```

Run unit tests:

```bash
make test
```

Start Redis and MongoDB:

```bash
make compose-up
```

Run the API locally in terminal 1:

```bash
make run
```

By default, `make run` starts the API at `http://localhost:8000`.

Set `PORT` to use another port:

```bash
PORT=9000 make run
```

Run the Celery background worker in terminal 2:

```bash
make celery-worker
```

This worker listens to the `transcriptions` queue. Upload requests create Celery tasks, but those tasks will not process unless this worker is running.

# **Run the full local API flow with automatic Docker cleanup:*

```bash
make local
```

This runs `make install`, `make test`, `make compose-up`, and then starts the API. When you stop the API with Ctrl-C, it automatically runs `make compose-down`. To process background jobs while `make local` is running, open a second terminal and run:

```bash
make celery-worker
```

Watch Redis container logs in another terminal:

```bash
make redis-logs
```

Watch Redis commands in real time:

```bash
make redis-monitor
```

Check how many jobs are waiting in the Celery queue:

```bash
make redis-queue
```

Check what the Celery worker is doing:

```bash
make celery-status
```

Build the app Docker image:

```bash
make build
```

Build and run the app Docker container:

```bash
make docker-run
```

Run the full local development flow:

```bash
make dev
```

Then run `make celery-worker` in a second terminal so queued background jobs are processed.

When you are done with local Docker services:

```bash
make compose-down
```

---

## Development

- `app/main.py` starts the FastAPI app.
- `app/tasks/celery_worker.py` configures Celery.
- `app/services/video/video_processing.py` orchestrates the processing flow.
- `docs/Complete_Flow_Diagram.md` documents the current request -> background flow.

---
Notes:

- `python run.py` launches uvicorn with `--reload` for development.
- If you run the app in Docker and link to `local-redis`, set `REDIS_URL` to `redis://redis:6379`.
- For production, prefer container orchestration (compose/kubernetes) and do not use `--link`.

## Docker usage

Docker is used to run supporting services (Redis, Mongo) and optionally the app itself.

- Container port vs host port: the container reads the `PORT` environment variable and binds Uvicorn to that port inside the container. When starting the container, map the host port to the container port with `-p host_port:container_port`.

- Example: run the app on host port `9000` by setting `PORT=9000` in the container and mapping the same host port:

```bash
docker run --rm -p 9000:9000 --name video-app --link local-redis:redis -e REDIS_URL=redis://redis:6379 -e PORT=9000 video-app
```

Inside the container the server binds to the value of `PORT` (for example `9000`) and the service will be available at `http://localhost:9000` on the host.

---

## Example .env

Create a `.env` file in the project root with the following variables (replace placeholders with real values):

```env
# MongoDB
MONGO_USERNAME=<your-mongo-username>
MONGO_PASSWORD=<your-mongo-password>
DATABASE_NAME=<your-database-name>
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>/<database>?retryWrites=true&w=majority

# Cloudflare R2
R2_ACCOUNT_ID=<your-r2-account-id>
R2_ACCESS_KEY_ID=<your-r2-access-key-id>
R2_SECRET_ACCESS_KEY=<your-r2-secret-access-key>
R2_BUCKET_NAME=<your-r2-bucket-name>

# Redis
REDIS_URL=redis://localhost:6379/0

# App settings
HOST=0.0.0.0
PORT=8000
RELOAD=true
ALLOWED_ORIGINS=http://localhost:4200
LOG_LEVEL=INFO


```

Keep this file out of version control. This repository already ignores `.env`.
