from abc import ABC, abstractmethod
from typing import List
from app.models.video_models import TranscriptItem

class SearchStrategy(ABC):
    @abstractmethod
    def search(self, query: str, transcript: List[TranscriptItem], video_url: str) -> List[dict]:
        pass

    def seconds_to_video_time(self, seconds: float) -> str:
        minutes, remaining_seconds = divmod(seconds, 60)

        video_time = f"{minutes:.0f}:{(remaining_seconds / 60):.2f}"

        return video_time
    