from typing import Dict, List, Optional, Any
from uuid import uuid4
from app.mongoDb.repository import VideoRepository
from app.constants import VideoStatus, Constants, StorageType, SearchStrategy as SearchStrategyEnum
from app.exceptions import VideoNotFoundException, InvalidYouTubeURLException, TranscriptNotFoundException
from app.schemas.video_schemas import UploadRequest, SearchQuery, SearchResponse, TranscriptSearchResult
from app.services.search import BasicSearch
from app.utils.validation_utils import extract_youtube_video_id, validate_video_id


class VideoService:
    def __init__(self, repository: VideoRepository, storage_service: Any = None) -> None:
        self.repository = repository
        self.storage_service = storage_service or self._create_storage_service()
        self.basic_search = BasicSearch()

    def _create_storage_service(self) -> Any:
        from app.services.storage.storage_service import StorageService
        return StorageService()

    def get_all_videos(self) -> List[Dict[str, Any]]:
        """Get all videos."""
        return self.repository.get_all_videos()

    def get_video(self, video_id: str) -> Dict[str, Any]:
        """Get video by ID."""
        validate_video_id(video_id)
        video = self.repository.get_video(video_id)
        if not video:
            raise VideoNotFoundException(video_id)
        return video

    def delete_video(self, video_id: str) -> None:
        """Delete video and cleanup storage."""
        video = self.get_video(video_id)

        if video.get("storage_type") == StorageType.R2.value and video.get("file_id"):
            self.storage_service.delete_file(video["file_id"])

        self.repository.delete_video(video_id)

    def upload(self, request: UploadRequest) -> str:
        """Register a new video by URL or R2 file ID."""
        if request.url:
            return self.upload_youtube_video(
                url=request.url,
                submission_id=request.submission_id,
                name=request.name,
                category=request.category,
                description=request.description,
            )

        if request.file_id:
            return self.upload_r2_video(request)

        raise ValueError("Either url or file_id must be provided")

    def upload_video(self, request: UploadRequest) -> str:
        """Backward compatible alias for upload()."""
        return self.upload(request)

    def upload_r2_video(self, request: UploadRequest) -> str:
        """Register metadata for a video already uploaded to R2."""
        self.storage_service.validate_existing_video_file(request.file_id)
        video_data: dict[str, Any] = {
            "submission_id": self.build_submission_id(request.submission_id),
            "name": request.name or "",
            "category": request.category or "",
            "description": request.description or "",
            "url": "",
            "file_id": request.file_id,
            "storage_type": StorageType.R2.value,
            "status": VideoStatus.QUEUED.value,
            "transcript": []
        }
        return self.repository.save_video(video_data)

    def upload_youtube_video(
        self,
        url: str,
        submission_id: Optional[str] = None,
        name: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Store YouTube video metadata directly in the database."""
        video_id = extract_youtube_video_id(url)
        video_data: dict[str, Any] = {
            "submission_id": self.build_submission_id(submission_id),
            "name": name or f"YouTube Video {video_id}",
            "category": category or "YouTube",
            "description": description or "",
            "url": url,
            "file_id": video_id,
            "storage_type": StorageType.YOUTUBE.value,
            "status": VideoStatus.QUEUED.value,
            "transcript": []
        }
        return self.repository.save_video(video_data)

    def build_submission_id(self, submission_id: Optional[str]) -> str:
        """Use caller-provided submission ID, or create one for this upload."""
        if submission_id and submission_id.strip():
            return submission_id.strip()
        return f"sub_{uuid4().hex}"

    def search_transcript(self, video_id: str, query: SearchQuery) -> SearchResponse:
        """Search video transcript."""
        video = self.get_video(video_id)
        transcript = video.get("transcript", [])

        if not transcript:
            raise TranscriptNotFoundException(video_id)

        if query.strategy == SearchStrategyEnum.SEMANTIC:
            from app.services.search.semantic_search import SemanticSearch

            semantic_search = SemanticSearch(Constants.semantic_model.value)
            results = semantic_search.search(query.query, transcript, video.get("url", ""), top_k=Constants.search_top_k)
        else:
            results: List[Dict[str, Any]] = self.basic_search.search(query.query, transcript, video.get("url", ""))

        search_results = [
            TranscriptSearchResult(
                timestamp=result.get("seconds", 0),
                text=result.get("text", ""),
                confidence=result.get("confidence")
            )
            for result in results
        ]

        return SearchResponse(
            results=search_results,
            total_results=len(search_results)
        )

    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL using shared validation utilities."""
        try:
            return extract_youtube_video_id(url)
        except InvalidYouTubeURLException:
            return None
