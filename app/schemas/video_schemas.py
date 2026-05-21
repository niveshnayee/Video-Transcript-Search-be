from pydantic import BaseModel, root_validator
from typing import List, Optional
from app.constants import SearchStrategy


class UploadRequest(BaseModel):
    """
    Unified upload request model.
    - `url`: optional YouTube URL
    - `file_id`: optional R2 object id
    - `name`, `category`, `description`: optional metadata
    """
    url: Optional[str] = None
    file_id: Optional[str] = None
    submission_id: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def validate_request(cls, values):
        url = values.get("url")
        file_id = values.get("file_id")
        if not url and not file_id:
            raise ValueError("Either `url` or `file_id` must be provided")
        return values


# Backwards-compatible alias for tests and existing imports.
VideoUploadRequest = UploadRequest


class SearchQuery(BaseModel):
    """
    Model for the transcript search query.
    - `query`: The text to search in the transcript.
    - `strategy`: Search strategy to use (basic or semantic).
    """
    query: str
    strategy: SearchStrategy = SearchStrategy.SEMANTIC


class UploadUrlRequest(BaseModel):
    """
    Model for generating upload URL request.
    - `file_name`: Name of the file to upload.
    - `file_size`: Size of the file in bytes.
    """
    file_name: str
    file_size: int


class UploadUrlResponse(BaseModel):
    """
    Response model for upload URL generation.
    - `upload_url`: The presigned URL for uploading the file.
    - `file_id`: Unique identifier for the file.
    """
    upload_url: str
    file_id: str


class VideoResponse(BaseModel):
    """
    Standard response model for video operations.
    - `success`: Whether the operation was successful.
    - `message`: Response message.
    - `data`: Optional data payload.
    """
    success: bool
    message: str
    data: Optional[dict] = None


class VideoListResponse(BaseModel):
    """
    Response model for listing videos.
    - `videos`: List of video summaries.
    """
    videos: List[dict]


class TranscriptSearchResult(BaseModel):
    """
    Model for transcript search results.
    - `timestamp`: Timestamp in the video.
    - `text`: The matching text.
    - `confidence`: Confidence score for semantic search.
    """
    timestamp: int
    text: str
    confidence: Optional[float] = None


class SearchResponse(BaseModel):
    """
    Response model for search operations.
    - `results`: List of search results.
    - `total_results`: Total number of results found.
    """
    results: List[TranscriptSearchResult]
    total_results: int


class TaskStatusResponse(BaseModel):
    """
    Response model for task status checking.
    - `task_id`: The task ID.
    - `status`: Current status of the task.
    - `result`: Task result if completed.
    """
    task_id: str
    status: str
    result: Optional[dict] = None
