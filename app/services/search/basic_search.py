from typing import List, Dict
from app.services.search.search_service import SearchStrategy


class BasicSearch(SearchStrategy):
    def search(self, query: str, transcript: List[Dict[str, any]], video_url: str) -> List[Dict[str, any]]:
        try:
            results: List[Dict[str, any]] = []
            query_lower = query.lower()
            for entry in transcript:
                text = entry.get("text", "")
                if query_lower in text.lower():
                    timestamp = entry.get("timestamp", 0)
                    results.append({
                        "seconds": timestamp,
                        "time": self.seconds_to_video_time(timestamp),
                        "text": text,
                        "video_link": f"{video_url}#t={int(timestamp)}s"
                    })
            return results
        except Exception as e:
            raise RuntimeError(f"Error in BasicSearch: {e}")

   