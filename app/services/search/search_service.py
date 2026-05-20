from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, query: str, transcript: List[Dict[str, Any]], video_url: str) -> List[Dict[str, Any]]:
        pass

    def seconds_to_video_time(self, seconds: float) -> str:
        minutes, remaining_seconds = divmod(seconds, 60)
        video_time = f"{minutes:.0f}:{(remaining_seconds / 60):.2f}"
        return video_time
    