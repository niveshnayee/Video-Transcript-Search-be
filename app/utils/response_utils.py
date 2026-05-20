from typing import Any, Dict, Optional
from app.schemas.video_schemas import VideoResponse


def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> VideoResponse:
    """Create a standardized success response."""
    return VideoResponse(
        success=True,
        message=message,
        data=data
    )


def create_error_response(
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> VideoResponse:
    """Create a standardized error response."""
    return VideoResponse(
        success=False,
        message=message,
        data=data
    )


def format_video_list(videos: list) -> list:
    """Format video list for API response."""
    formatted = []
    for video in videos:
        formatted.append({
            "video_id": str(video["_id"]),
            "submission_id": video.get("submission_id"),
            "name": video["name"],
            "category": video["category"],
            "description": video["description"],
            "url": video.get("url"),
            "status": video.get("status")
        })
    return formatted


def format_video_details(video: Dict[str, Any]) -> Dict[str, Any]:
    """Format video details for API response."""
    return {
        "video_id": str(video["_id"]),
        "submission_id": video.get("submission_id"),
        "name": video["name"],
        "category": video["category"],
        "description": video["description"],
        "url": video.get("url"),
        "status": video.get("status"),
        "transcript": video.get("transcript", [])
    }
