from typing import Generator
from fastapi import Depends
from app.mongoDb.connection import MongoDBClient
from app.mongoDb.repository import VideoRepository
from app.services.video.video_service import VideoService


def get_mongo_client() -> Generator[MongoDBClient, None, None]:
    """Dependency to get MongoDB client."""
    client = MongoDBClient()
    try:
        yield client
    finally:
        # MongoDB client handles connection pooling automatically
        pass


def get_video_repository(
    mongo_client: MongoDBClient = Depends(get_mongo_client)
) -> VideoRepository:
    """Dependency to get video repository."""
    collection = mongo_client.get_collection("Video_Transcript")
    return VideoRepository(collection)


def get_video_service(
    repository: VideoRepository = Depends(get_video_repository)
) -> VideoService:
    """Dependency to get video service."""
    return VideoService(repository)