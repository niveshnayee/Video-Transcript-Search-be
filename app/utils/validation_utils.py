from typing import Optional
from app.constants import Constants
from app.exceptions import InvalidYouTubeURLException


def validate_youtube_url(url: str) -> bool:
    """Validate if a URL is a valid YouTube URL."""
    if not url or not isinstance(url, str):
        return False

    url_lower = url.lower()
    return (
        url_lower.startswith(('http://', 'https://')) and
        ('youtube.com' in url_lower or 'youtu.be' in url_lower)
    )


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    import re

    if not validate_youtube_url(url):
        raise InvalidYouTubeURLException(url)

    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise InvalidYouTubeURLException(url)


def validate_file_size(file_size: int) -> None:
    """Validate file size against limits."""
    from app.exceptions import FileTooLargeException

    if file_size > Constants.max_file_size_bytes:
        raise FileTooLargeException(file_size, Constants.max_file_size_bytes)


def validate_file_extension(filename: str) -> None:
    """Validate file extension against allowed types."""
    from app.exceptions import InvalidFileTypeException
    import os

    _, ext = os.path.splitext(filename.lower())
    if ext not in Constants.allowed_video_extensions:
        raise InvalidFileTypeException(ext)


def validate_video_id(video_id: str) -> None:
    """Validate video ID format."""
    from app.exceptions import InvalidVideoIdException
    from bson import ObjectId

    try:
        ObjectId(video_id)
    except Exception:
        raise InvalidVideoIdException(video_id)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters."""
    import re
    import os

    # Remove path separators
    filename = os.path.basename(filename)

    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext

    return filename