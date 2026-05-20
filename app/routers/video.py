from fastapi import APIRouter, HTTPException, Depends
from celery.result import AsyncResult
from app.dependencies import get_video_service
from app.services.video.video_service import VideoService
from app.schemas.video_schemas import UploadRequest, VideoResponse, VideoListResponse, SearchQuery, SearchResponse, TaskStatusResponse
from app.exceptions import AppException
from app.logging_config import get_logger
from app.utils.response_utils import format_video_list, format_video_details
from app.tasks.celery_worker import celery

logger = get_logger(__name__)
router = APIRouter()


@router.get("/videos", response_model=VideoListResponse)
async def get_all_videos(service: VideoService = Depends(get_video_service)):
    """Get a list of all uploaded videos with metadata."""
    try:
        videos = service.get_all_videos()
        return VideoListResponse(videos=format_video_list(videos))
    except AppException as e:
        logger.error(f"Error fetching videos: {e.message}", extra={"extra_fields": {"error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error fetching videos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/video/{video_id}")
async def get_video_details(video_id: str, service: VideoService = Depends(get_video_service)):
    """Get the details of a specific video by its ID."""
    try:
        video = service.get_video(video_id)
        return VideoResponse(
            success=True,
            message="Video details fetched successfully",
            data=format_video_details(video)
        )
    except AppException as e:
        logger.error(f"Error fetching video {video_id}: {e.message}", extra={"extra_fields": {"video_id": video_id, "error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error fetching video {video_id}: {str(e)}", exc_info=True, extra={"extra_fields": {"video_id": video_id}})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/video/{video_id}")
async def delete_video(video_id: str, service: VideoService = Depends(get_video_service)):
    """Delete a video and clean up associated resources."""
    try:
        service.delete_video(video_id)
        return VideoResponse(success=True, message="Video deleted successfully")
    except AppException as e:
        logger.error(f"Error deleting video {video_id}: {e.message}", extra={"extra_fields": {"video_id": video_id, "error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error deleting video {video_id}: {str(e)}", exc_info=True, extra={"extra_fields": {"video_id": video_id}})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/video/{video_id}/search", response_model=SearchResponse)
async def search_video_transcript(video_id: str, query: SearchQuery, service: VideoService = Depends(get_video_service)):
    """Search through a video's transcript."""
    try:
        result = service.search_transcript(video_id, query)
        return result
    except AppException as e:
        logger.error(f"Error searching transcript for video {video_id}: {e.message}", extra={"extra_fields": {"video_id": video_id, "query": query.query, "error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error searching transcript for video {video_id}: {str(e)}", exc_info=True, extra={"extra_fields": {"video_id": video_id, "query": query.query}})
        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/upload", response_model=VideoResponse)
async def unified_upload(request: UploadRequest, service: VideoService = Depends(get_video_service)):
    """Unified upload endpoint for both YouTube URLs and R2 file uploads."""
    try:
        video_id = service.upload(request)
        video = service.get_video(video_id)
        submission_id = video.get("submission_id")
        task = celery.send_task(
            "app.services.video.video_processing.process_video_background_task",
            args=[video_id],
            queue="transcriptions",
        )
        logger.info(
            "Queued video processing task",
            extra={"extra_fields": {"video_id": video_id, "submission_id": submission_id, "task_id": task.id, "queue": "transcriptions"}},
        )
        return VideoResponse(
            success=True,
            message="Upload registered",
            data={"video_id": video_id, "submission_id": submission_id, "task_id": task.id, "queue": "transcriptions"},
        )
    except AppException as e:
        logger.error(f"Upload error: {e.message}", extra={"extra_fields": {"error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Check the status of a Celery background task."""
    try:
        task = AsyncResult(task_id, app=celery)
        result = task.result if task.successful() and isinstance(task.result, dict) else None
        return TaskStatusResponse(task_id=task_id, status=task.status, result=result)
    except Exception as e:
        logger.error(f"Unexpected task status error: {str(e)}", exc_info=True, extra={"extra_fields": {"task_id": task_id}})
        raise HTTPException(status_code=500, detail="Internal server error")
