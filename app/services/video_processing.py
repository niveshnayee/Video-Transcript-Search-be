
import logging
from pathlib import Path
from app.utils.video_utils import VideoUtils
from app.services.transcription_api import TranscriptionService
from app.utils.file_cleanup import FileCleanup
from app.database import MongoDBClient
from bson import ObjectId
from app.tasks.celery_worker import celery




class VideoProcessingService:
    def __init__(self):
        self.db_client = MongoDBClient()
        self.videos_collection = self.db_client.get_collection("videos")

    @celery.task(bind=True, name="app.services.video_processing.process_video_from_url", retry_backoff=5, max_retries=3)
    def process_video_from_url(self, file_id: str, video_url: str):
        """
        Process an uploaded video URL by extracting audio and generating a transcript.
        """
        video_path = None
        audio_path = None

        try:
            # Update the video status to "processing"
            self.videos_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"status": "processing"}}
            )

            # Save the video locally
            video_path = VideoUtils.save_uploaded_video(video_url)

            # Extract audio from the video
            audio_path = str(Path(video_path).with_suffix(".wav"))
            VideoUtils.extract_audio(video_path, audio_path)

            # Generate a transcript from the audio
            transcript = TranscriptionService.transcribe_audio_with_timestamps(audio_path)

            # Update the video status to "completed" and save the transcript
            self.videos_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"status": "completed", "transcript": transcript}}
            )
        except Exception as e:
            # Log the error and update the video status to "failed"
            logging.error(f"Error processing video {file_id}: {str(e)}", exc_info=True)
            self.videos_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"status": "failed"}}
            )
        finally:
            # Clean up temporary files
            FileCleanup.cleanup_temp_files([video_path, audio_path])



    #@celery.task(bind=True, name="app.services.video_processing.process_video_from_url", retry_backoff=5, max_retries=3)
