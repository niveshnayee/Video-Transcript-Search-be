from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, VideoUnavailable


def get_youtube_transcript(video_id: str):
    """
    Fetch the transcript for a YouTube video using the YouTubeTranscriptApi.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return [{"timestamp": entry["start"], "text": entry["text"]} for entry in transcript]
    except NoTranscriptFound:
        raise Exception("No transcript found for this video.")
    except VideoUnavailable:
        raise Exception("Video is unavailable.")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")
