import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Define Celery app
celery = Celery(
    "worker",
    broker=redis_url,  # Redis as the message broker
    backend=redis_url,  # Store results in Redis
)

celery.conf.update(
    task_default_queue="transcriptions",
    task_routes={
        "app.services.video.video_processing.process_video_background_task": {
            "queue": "transcriptions"
        }
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,  # Task results expire in 1 hour
)

# Import the module that registers the video processing task.
celery.conf.imports = ("app.services.video.video_processing",)
