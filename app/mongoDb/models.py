from pydantic import BaseModel
from typing import List, Optional
from app.constants import VideoStatus, StorageType


class TranscriptItem(BaseModel):
    timestamp: int
    text: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class VideoCreate(BaseModel):
    submission_id: str
    name: str
    category: str
    description: str
    url: str  # URL
    file_id: str
    storage_type: StorageType = StorageType.R2
    status: VideoStatus = VideoStatus.QUEUED
    transcript: Optional[List[TranscriptItem]] = []  # List of TranscriptItem objects


class VideoDocument(VideoCreate):
    _id: Optional[str] = None


class VideoResponse(BaseModel):
    success: bool
    message: str
