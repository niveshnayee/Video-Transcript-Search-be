from typing import Optional, Dict, Any
from app.constants import Constants


class AppException(Exception):
    """Base exception class for the application."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[str] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to standardized response format."""
        response = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


class VideoNotFoundException(AppException):
    def __init__(self, video_id: str) -> None:
        super().__init__(
            message=Constants.ERROR_VIDEO_NOT_FOUND,
            code="VIDEO_NOT_FOUND",
            status_code=404,
            details=f"Video with ID {video_id} not found"
        )


class InvalidVideoIdException(AppException):
    def __init__(self, video_id: str) -> None:
        super().__init__(
            message=Constants.ERROR_INVALID_VIDEO_ID,
            code="INVALID_VIDEO_ID",
            status_code=400,
            details=f"Invalid video ID format: {video_id}"
        )


class TranscriptNotFoundException(AppException):
    def __init__(self, video_id: str) -> None:
        super().__init__(
            message=Constants.ERROR_TRANSCRIPT_NOT_FOUND,
            code="TRANSCRIPT_NOT_FOUND",
            status_code=404,
            details=f"No transcript available for video {video_id}"
        )


class StorageLimitExceededException(AppException):
    def __init__(self) -> None:
        super().__init__(
            message=Constants.ERROR_STORAGE_LIMIT_EXCEEDED,
            code="STORAGE_LIMIT_EXCEEDED",
            status_code=413
        )


class FileTooLargeException(AppException):
    def __init__(self, file_size: int, max_size: int) -> None:
        super().__init__(
            message=Constants.ERROR_FILE_TOO_LARGE,
            code="FILE_TOO_LARGE",
            status_code=413,
            details=f"File size {file_size} bytes exceeds maximum {max_size} bytes"
        )


class InvalidFileTypeException(AppException):
    def __init__(self, file_extension: str) -> None:
        super().__init__(
            message=Constants.ERROR_INVALID_FILE_TYPE,
            code="INVALID_FILE_TYPE",
            status_code=400,
            details=f"File type {file_extension} is not allowed"
        )


class InvalidYouTubeURLException(AppException):
    def __init__(self, url: str) -> None:
        super().__init__(
            message=Constants.ERROR_YOUTUBE_URL_INVALID,
            code="YOUTUBE_URL_INVALID",
            status_code=400,
            details=f"Invalid YouTube URL: {url}"
        )


class TranscriptionFailedException(AppException):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(
            message=Constants.ERROR_TRANSCRIPTION_FAILED,
            code="TRANSCRIPTION_FAILED",
            status_code=500,
            details=details
        )


class SearchFailedException(AppException):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(
            message=Constants.ERROR_SEARCH_FAILED,
            code="SEARCH_FAILED",
            status_code=500,
            details=details
        )


class UploadFailedException(AppException):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(
            message=Constants.ERROR_UPLOAD_FAILED,
            code="UPLOAD_FAILED",
            status_code=500,
            details=details
        )


class DuplicateSubmissionIdException(AppException):
    def __init__(self, submission_id: str) -> None:
        super().__init__(
            message="Duplicate submission ID",
            code="DUPLICATE_SUBMISSION_ID",
            status_code=409,
            details=f"Submission ID {submission_id} already exists"
        )


class ProcessingFailedException(AppException):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(
            message=Constants.ERROR_PROCESSING_FAILED,
            code="PROCESSING_FAILED",
            status_code=500,
            details=details
        )


class DatabaseConnectionException(AppException):
    def __init__(self) -> None:
        super().__init__(
            message=Constants.ERROR_DATABASE_CONNECTION,
            code="DATABASE_CONNECTION_ERROR",
            status_code=500
        )


class RedisConnectionException(AppException):
    def __init__(self) -> None:
        super().__init__(
            message=Constants.ERROR_REDIS_CONNECTION,
            code="REDIS_CONNECTION_ERROR",
            status_code=500
        )


class R2ConnectionException(AppException):
    def __init__(self) -> None:
        super().__init__(
            message=Constants.ERROR_R2_CONNECTION,
            code="R2_CONNECTION_ERROR",
            status_code=500
        )
