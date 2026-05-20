import logging
from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List, Dict, Any
from app.services.search.search_service import SearchStrategy
from app.constants import Constants

logger = logging.getLogger(__name__)


class SemanticSearch(SearchStrategy):
    def __init__(self, model_name: str = Constants.semantic_model.value) -> None:
        self.model = SentenceTransformer(model_name)

        # Validate model initialization
        if not hasattr(self.model, 'encode'):
            raise ValueError("Invalid model - must implement encode() method")

    def search(self, query: str, transcript: List[Dict[str, Any]], video_url: str, top_k: int = 3) -> List[Dict[str, Any]]:
        try:
            if not query or not transcript:
                logger.warning("Empty query or transcript received")
                return []

            query_embedding = self.model.encode(
                query,
                convert_to_tensor=True,
            )

            transcript_texts = [item.get("text", "") for item in transcript]
            timestamps = [item.get("timestamp", 0) for item in transcript]

            transcript_embeddings = self.model.encode(
                transcript_texts,
                convert_to_tensor=True,
            )

            similarities = util.cos_sim(query_embedding, transcript_embeddings)[0].cpu().numpy()
            similarities = np.nan_to_num(similarities, nan=0.0)

            valid_indices = np.argsort(similarities)[::-1][:top_k]

            results: List[Dict[str, Any]] = []
            for idx in valid_indices:
                if idx < len(transcript):
                    timestamp = timestamps[idx]
                    results.append({
                        "seconds": timestamp,
                        "time": self.seconds_to_video_time(timestamp),
                        "text": transcript_texts[idx],
                        "video_link": f"{video_url}#t={int(timestamp)}s",
                        "confidence": round(float(similarities[idx]), 3)
                    })

            return results

        except Exception as e:
            raise RuntimeError(f"Error in SemanticSearch: {e}")