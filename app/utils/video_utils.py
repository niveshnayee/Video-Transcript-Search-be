import requests
from fastapi import HTTPException
import os
from pathlib import Path
from tempfile import gettempdir
from moviepy.editor import VideoFileClip
from yt_dlp import YoutubeDL

import re


def save_uploaded_video(video_url) -> str:
    """
    Save an uploaded video file to a temporary directory.

    Args:
        file (UploadFile): The uploaded file object.

    Returns:
        str: The path to the saved video file.
    """
    try:
        # Create a temporary directory for storing the uploaded video
        temp_dir = Path(gettempdir()) / "uploaded_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract filename from URL
        filename = video_url.split("/")[-1]
        # Sanitize the file name (remove spaces and special characters)
        sanitized_filename = re.sub(r'[^\w\-_\.]', '_', filename)

        # Define the file path
        file_path = temp_dir / sanitized_filename

        # Download video
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        # Save the file to the temporary directory
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return str(file_path)

    except Exception as e:
        raise Exception(f"Failed to save uploaded video: {str(e)}")


def extract_audio(video_path: str, output_audio_path: str):
    """
    Extract audio from a video file.
    """
    try:
        if not video_path or not output_audio_path:
            raise ValueError("Invalid paths provided for video or audio extraction")

        clip = VideoFileClip(video_path)
        if not clip.audio:
            raise HTTPException(status_code=400, detail="Video file has no audio track")

        clip.audio.write_audiofile(
            output_audio_path, 
            codec='pcm_s16le',
            verbose=True,  # Add this to enable detailed FFmpeg logs
            logger="bar"   # This will show the MoviePy progress bar
            )

        clip.close()  # Ensure resources are released
        return output_audio_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract audio: {str(e)}")
    finally:
        if 'clip' in locals():
            clip.close()  # Clean up MoviePy resources


def download_youtube_video_audio(video_url: str, output_path: str):
    """
    Download the audio of a YouTube video using yt-dlp.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(video_url, download=True)
    return output_path