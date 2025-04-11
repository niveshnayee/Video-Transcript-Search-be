from abc import ABC, abstractmethod
from typing import List
from app.models.video_models import TranscriptSegment

class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        """Transcribe audio and return timed segments"""
        pass

    @abstractmethod
    def format_transcript(self, segments: List[TranscriptSegment]) -> dict:
        """Format transcript for storage"""
        pass