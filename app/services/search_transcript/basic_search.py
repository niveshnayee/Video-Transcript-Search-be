from app.services.search_transcript.search_service import SearchStrategy
from app.models.video_models import TranscriptItem
from typing import List


class BasicSearch(SearchStrategy):
    def search(self, query: str, transcript: List[TranscriptItem], video_url: str) -> List[dict]:
        try:

            results = []
            for entry in transcript:
                if query in entry["text"].lower():
                    results.append({
                        "seconds": entry["timestamp"],
                        "time": self.seconds_to_video_time(entry["timestamp"]),
                        "text": entry["text"],
                        "video_link": f"{video_url}#t={int(entry['timestamp'])}s"
                    })
            return results
        except Exception as e:
            print(f"Error in BasicSearch: {e}")
            

   