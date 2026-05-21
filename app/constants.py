from enum import Enum
from typing import List


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class WhisperModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class SemanticModel(str, Enum):
    ALL_MINI_LM_L6_V2 = "all-MiniLM-L6-v2"


class SearchStrategy(str, Enum):
    BASIC = "basic"
    SEMANTIC = "semantic"


class VideoStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StorageType(str, Enum):
    R2 = "r2"
    YOUTUBE = "youtube"


class Constants:
    # ── File / Storage limits
    max_file_size_bytes: int = 1 * 1024 * 1024 * 1024  # 1 GB
    max_total_storage_bytes: int = 9 * 1024 * 1024 * 1024  # 9 GB
    allowed_video_extensions: List[str] = [
        ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"
    ]

    # ── ML Models
    whisper_model_size: WhisperModelSize = WhisperModelSize.BASE
    semantic_model: SemanticModel = SemanticModel.ALL_MINI_LM_L6_V2
    search_top_k: int = 3
    batch_size: int = 32

    # ── Logging
    log_level: LogLevel = LogLevel.INFO

    # ── Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    result_expiration_seconds: int = 3600

    # ── R2 Storage
    signature_version: str = "s3v4"
    content_type_video: str = "video/mp4"
    presigned_url_expiration_minutes: int = 15

    # ── YouTube/Audio
    yt_dlp_format: str = "bestaudio/best"
    http_chunk_size: int = 8192

    # ── Exception Messages
    ERROR_VIDEO_NOT_FOUND: str = "Video not found"
    ERROR_INVALID_VIDEO_ID: str = "Invalid video ID"
    ERROR_TRANSCRIPT_NOT_FOUND: str = "Transcript not found for this video"
    ERROR_STORAGE_LIMIT_EXCEEDED: str = "Storage limit exceeded"
    ERROR_FILE_TOO_LARGE: str = "File size exceeds maximum allowed limit"
    ERROR_INVALID_FILE_SIZE: str = "File size must be greater than zero"
    ERROR_INVALID_FILE_TYPE: str = "Invalid file type. Only video files are allowed"
    ERROR_YOUTUBE_URL_INVALID: str = "Invalid YouTube URL"
    ERROR_TRANSCRIPTION_FAILED: str = "Transcription failed"
    ERROR_SEARCH_FAILED: str = "Search operation failed"
    ERROR_UPLOAD_FAILED: str = "File upload failed"
    ERROR_PROCESSING_FAILED: str = "Video processing failed"
    ERROR_DATABASE_CONNECTION: str = "Database connection error"
    ERROR_REDIS_CONNECTION: str = "Redis connection error"
    ERROR_R2_CONNECTION: str = "R2 storage connection error"
