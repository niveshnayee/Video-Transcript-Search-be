import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.utils.video_utils import VideoUtils
from app.utils.file_cleanup import FileCleanup
from app.mongoDb.repository import VideoRepository
from app.services.storage.storage_service import StorageService
from app.services.transcription.whisper_transcription import WhisperTranscriptionService

from app.constants import Constants, VideoStatus
from app.models.video_models import TranscriptSegment
from app.mongoDb.models import TranscriptItem
from app.tasks.celery_worker import celery

logger = logging.getLogger(__name__)


class VideoProcessingService:
    def __init__(
        self,
        video_utils: VideoUtils,
        file_cleanup: FileCleanup,
        transcription_service: WhisperTranscriptionService,
        video_repo: VideoRepository,
        storage_service: StorageService,
    ) -> None:
        self.video_utils: VideoUtils = video_utils
        self.file_cleanup: FileCleanup = file_cleanup
        self.transcription_service: WhisperTranscriptionService = transcription_service
        self.video_repo: VideoRepository = video_repo
        self.storage_service: StorageService = storage_service

    def process_video(self, video_id: str) -> Dict[str, str]:
        """Main entry for processing a video document by id.

        This fetches video metadata, determines storage type (R2 or YouTube),
        downloads the source to a temp directory, extracts audio, transcribes,
        saves transcript and updates status. Helper operations are delegated
        to `VideoUtils`, `StorageService` and `FileCleanup`.
        """
        video_path = None
        audio_path = None

        try:
            self.mark_processing(video_id)

            video = self.video_repo.get_video(video_id)
            if not video:
                raise Exception(f"Video metadata not found for id={video_id}")

            storage_type = video.get("storage_type")

            # prepare temp directory
            from tempfile import gettempdir
            temp_dir = Path(gettempdir()) / f"video_processing_{video_id}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            if storage_type == "r2":
                # download file from R2
                object_name = video.get("file_id")
                if not object_name:
                    raise Exception("Missing file_id for R2 stored video")
                dest = temp_dir / object_name
                self.storage_service.download_file(object_name, str(dest))
                video_path = str(dest)

            elif storage_type == "youtube":
                # download audio/video using yt-dlp and extract metadata
                from yt_dlp import YoutubeDL

                url = video.get("url")
                if not url:
                    raise Exception("Missing URL for YouTube video")

                ydl_opts = {
                    'format': Constants.yt_dlp_format,
                    'outtmpl': str(temp_dir / '%(id)s.%(ext)s'),
                    'quiet': True,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                video_path = str(temp_dir / f"{info['id']}.{info.get('ext','mp4')}")

                # update title/description when available
                metadata = {}
                if info.get('title'):
                    metadata['name'] = info.get('title')
                if info.get('description'):
                    metadata['description'] = info.get('description')
                if metadata:
                    try:
                        self.video_repo.update_fields(video_id, metadata)
                    except Exception:
                        logger.debug("Failed to update video metadata, continuing")

            else:
                raise Exception(f"Unsupported storage type: {storage_type}")

            # audio extraction and transcription (shared path)
            audio_path = self.build_audio_path(video_path)
            self.extract_audio(video_path, audio_path)

            segments = self.transcribe_audio(audio_path)
            transcript = self.build_searchable_transcript(segments)

            self.save_transcript(video_id, transcript)
            self.mark_completed(video_id)

            return {"video_id": video_id, "status": "success"}
        except Exception as exc:
            self.mark_failed(video_id, exc)
            raise
        finally:
            self.cleanup_temp_files(video_path, audio_path)

    def mark_processing(self, video_id: str) -> None:
        self.update_status(video_id, VideoStatus.PROCESSING)

    def mark_completed(self, video_id: str) -> None:
        self.update_status(video_id, VideoStatus.COMPLETED)

    def mark_failed(self, video_id: str, exc: Exception) -> None:
        logger.error("Error processing video %s: %s", video_id, exc, exc_info=True)
        self.update_status(video_id, VideoStatus.FAILED)

    def update_status(self, video_id: str, status: VideoStatus) -> None:
        self.video_repo.update_status(video_id, status)

    def build_audio_path(self, video_path: str) -> str:
        return str(Path(video_path).with_suffix(".wav"))

    def extract_audio(self, video_path: str, audio_path: str) -> str:
        return self.video_utils.extract_audio(video_path, audio_path)

    def transcribe_audio(self, audio_path: str) -> List[TranscriptSegment]:
        return self.transcription_service.transcribe(audio_path)

    def build_searchable_transcript(
        self,
        segments: List[TranscriptSegment],
    ) -> List[TranscriptItem]:
        return [
            TranscriptItem(timestamp=int(segment.start), text=segment.text)
            for segment in segments
        ]

    def save_transcript(
        self,
        video_id: str,
        transcript: List[TranscriptItem],
    ) -> None:
        self.video_repo.add_transcript(video_id, transcript)

    def cleanup_temp_files(
        self,
        video_path: Optional[str],
        audio_path: Optional[str],
    ) -> None:
        paths = [path for path in [video_path, audio_path] if path]
        self.file_cleanup.cleanup_temp_files(paths)


def create_video_processing_service() -> VideoProcessingService:
    from app.mongoDb.connection import MongoDBClient
    from app.mongoDb.repository import VideoRepository
    from app.services.storage.storage_service import StorageService
    from app.services.transcription.whisper_transcription import WhisperTranscriptionService

    mongo_client = MongoDBClient()
    collection = mongo_client.get_collection("Video_Transcript")

    return VideoProcessingService(
        video_utils=VideoUtils(),
        file_cleanup=FileCleanup(),
        transcription_service=WhisperTranscriptionService(),
        video_repo=VideoRepository(collection),
        storage_service=StorageService(),
    )


@celery.task(
    bind=True,
    name="app.services.video.video_processing.process_video_background_task",
    retry_backoff=5,
    max_retries=3,
)
def process_video_background_task(self: Any, video_id: str) -> Dict[str, str]:
    service = create_video_processing_service()
    try:
        return service.process_video(video_id)
    except Exception as exc:
        raise self.retry(exc=exc) from exc
