from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, query: str, transcript: List[Dict[str, Any]], video_url: str) -> List[Dict[str, Any]]:
        pass

    def seconds_to_video_time(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        minutes, remaining_seconds = divmod(total_seconds, 60)
        return f"{minutes}:{remaining_seconds:02d}"
    
