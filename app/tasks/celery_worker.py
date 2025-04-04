from celery import Celery

# Define Celery app
celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",  # Redis as the message broker
    backend="redis://localhost:6379/0",  # Store results in Redis
)

celery.conf.update(
    task_routes={"app.services.video_processing.process_video_from_url": {"queue": "transcriptions"}},
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,  # Task results expire in 1 hour
)

# Automatically discover tasks in the `app.services` module
celery.autodiscover_tasks(["app.services.video_processing"])
