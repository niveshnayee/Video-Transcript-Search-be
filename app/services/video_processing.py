
import logging
from pathlib import Path
from app.utils.video_utils import VideoUtils
from app.tasks.celery_worker import celery




class VideoProcessingService:
    def __init__(self, video_utils, file_cleanup, transcription_service, video_repo):
        self.video_utils = video_utils
        self.file_cleanup = file_cleanup
        self.transcription_service = transcription_service
        self.video_repo = video_repo

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
            video_path = self.video_utils.save_uploaded_video(video_url)

            # Extract audio from the video
            audio_path = str(Path(video_path).with_suffix(".wav"))
            self.video_utils.extract_audio(video_path, audio_path)

            # Generate a transcript from the audio
            segmets = self.transcription_service.transcribe(audio_path)
            transcript = self.transcription_service.format_transcript(segments)


            self.video_repo.add_transcript(file_id, transcript)
            self.video_repo.update_status(file_id, "completed")


            return {"video_id": video_id, "status": "success"}

            
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
