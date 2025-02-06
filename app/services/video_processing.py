
import logging
from pathlib import Path
from app.utils.video_utils import download_youtube_video_audio, extract_audio, save_uploaded_video
from fastapi import HTTPException, UploadFile, BackgroundTasks

from app.services.youtube_transcript import get_youtube_transcript
from app.services.transcription_api import transcribe_audio_free_api, transcribe_audio_with_timestamps
from urllib.parse import urlparse, parse_qs
from app.utils.file_cleanup import cleanup_temp_files
from app.database import videos_collection
from bson import ObjectId



logging.basicConfig(
    filename="app.log",  # Log file location
    level=logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",
)



async def process_video_from_url(file_id: str, video_url: str):
    """
    Process an uploaded video file by extracting audio and generating a transcript.
    """

    # Initialize variables to ensure they are defined even if an exception occurs
    video_path = None
    audio_path = None

    try:
        video_path = save_uploaded_video(video_url)
        logging.info(f"Saved video to: {video_path}")

        # # Ensure the audio path is properly derived
        # if not video_path.endswith(".mp4"):
        #     raise ValueError("Uploaded file is not an .mp4 file")
        
        audio_path = str(Path(video_path).with_suffix(".wav"))

        # Save the uploaded file to a temporary location

        extract_audio(video_path, audio_path)
        logging.info(f"Extracted audio to: {audio_path}")

        transcript = transcribe_audio_with_timestamps(audio_path)
        logging.info(f"Generated transcript: {transcript}")
        
        cleanup_temp_files([video_path, audio_path])

        # Step 2: Update MongoDB with the transcript
        video = videos_collection.find_one({"_id": ObjectId(file_id)})
        if video:
            videos_collection.update_one(
                {"_id": ObjectId(file_id)},  # updating the correct document
                {"$set": {"transcript": transcript}}
            )
            logging.info(f"Transcript for {file_id} saved successfully.")
            # print(f"Transcript for {file_id} saved successfully.")
        else:
            logging.error(f"Video with file_id {file_id} not found in DB")
            # print(f"Video with file_id {file_id} not found in DB")


        # return {"method": "transcription_api", "Transcript": transcript}
    except Exception as e:
        logging.error(f"Error processing video {file_id}: {str(e)}", exc_info=True)  # Log stack trace
    # finally:
    #     cleanup_temp_files([video_path, audio_path])