import requests
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import gettempdir
from yt_dlp import YoutubeDL

import re

class VideoUtils:
    HOMEBREW_FFMPEG_PATHS = (
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    )

    @staticmethod
    def get_ffmpeg_executable() -> str:
        """Find an ffmpeg executable from PATH, Homebrew, or imageio-ffmpeg."""
        ffmpeg_path = os.getenv("FFMPEG_BINARY")
        if ffmpeg_path and Path(ffmpeg_path).exists():
            return ffmpeg_path

        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path

        for candidate in VideoUtils.HOMEBREW_FFMPEG_PATHS:
            if Path(candidate).exists():
                return candidate

        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as e:
            raise RuntimeError(
                "ffmpeg is required to extract audio but was not found. "
                "Install it with 'brew install ffmpeg' or run 'uv pip install -r requirements.txt'."
            ) from e

    @staticmethod
    def save_uploaded_video(video_url: str) -> str:
        """
        Save an uploaded video file to a temporary directory.
        """
        try:
            temp_dir = Path(gettempdir()) / "uploaded_videos"
            temp_dir.mkdir(parents=True, exist_ok=True)

            filename = video_url.split("/")[-1]
            sanitized_filename = re.sub(r'[^\w\-_\.]', '_', filename)
            file_path = temp_dir / sanitized_filename

            response = requests.get(video_url, stream=True)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return str(file_path)
        except Exception as e:
            raise Exception(f"Failed to save uploaded video: {str(e)}")


    @staticmethod
    def extract_audio(video_path: str, output_audio_path: str):
        """
        Extract audio from a video file.
        """
        try:
            if not video_path or not output_audio_path:
                raise ValueError("Invalid paths provided for video or audio extraction")

            output_path = Path(output_audio_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ffmpeg = VideoUtils.get_ffmpeg_executable()

            command = [
                ffmpeg,
                "-y",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                output_audio_path,
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                error_output = result.stderr.strip() or result.stdout.strip()
                raise RuntimeError(error_output or "ffmpeg failed to extract audio")

            return output_audio_path
        except FileNotFoundError as e:
            raise RuntimeError(
                "ffmpeg is required to extract audio but was not found. "
                "Install it with 'brew install ffmpeg' or run 'uv pip install -r requirements.txt'."
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio: {str(e)}") from e

    @staticmethod
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
