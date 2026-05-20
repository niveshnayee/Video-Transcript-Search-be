from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Dict, List, Optional, Any
from app.mongoDb.models import VideoDocument, TranscriptItem
from app.constants import VideoStatus
from app.exceptions import DuplicateSubmissionIdException


class VideoRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Ensure submission IDs are unique for all new video documents."""
        self.collection.create_index(
            "submission_id",
            unique=True,
            sparse=True,
            name="unique_submission_id",
        )

    def save_video(self, video_data: Dict[str, Any]) -> str:
        """Save video metadata to the database."""
        try:
            result = self.collection.insert_one(video_data)
            return str(result.inserted_id)
        except DuplicateKeyError as exc:
            submission_id = str(video_data.get("submission_id", ""))
            raise DuplicateSubmissionIdException(submission_id) from exc

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve video metadata by ID."""
        return self.collection.find_one({"_id": ObjectId(video_id)})

    def update_status(self, video_id: str, status: VideoStatus) -> None:
        self.collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"status": status.value}}
        )

    def add_transcript(self, video_id: str, transcript: List[TranscriptItem]) -> None:
        self.collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"transcript": [item.dict() for item in transcript]}}
        )

    def delete_video(self, video_id: str) -> None:
        self.collection.delete_one({"_id": ObjectId(video_id)})

    def get_all_videos(self) -> List[Dict[str, Any]]:
        return list(self.collection.find())

    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve transcript by video ID."""
        return self.collection.find_one({"_id": ObjectId(video_id)})
    
    def update_fields(self, video_id: str, fields: dict) -> None:
        """Update arbitrary fields on a video document."""
        self.collection.update_one({"_id": ObjectId(video_id)}, {"$set": fields})
