from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List
from app.models.video_models import TranscriptItem
from app.services.search_transcript.search_service import SearchStrategy


class SemanticSearch(SearchStrategy):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        # self._cache = {}

        # Validate model initialization
        if not hasattr(self.model, 'encode'):
            raise ValueError("Invalid model - must implement encode() method")

    def search(self, query: str, transcript: List[TranscriptItem], video_url: str, top_k: int = 3) -> List[dict]:
        try:
            if not query or not transcript:
                logger.warning("Empty query or transcript received")
                return []
            
            query_embedding = self.model.encode(
                    query, 
                    convert_to_tensor=True,
                )
            
            # Access dictionary keys instead of attributes
            transcript_texts = [item["text"] for item in transcript if "text" in item]
            timestamps = [item["timestamp"] for item in transcript if "timestamp" in item]
            
            # cache_key = hash(tuple(transcript_texts))
            # if cache_key not in self._cache:
            #     self._cache[cache_key] = self.model.encode(
            #                                 transcript_texts, 
            #                                 convert_to_tensor=True,
            #                                 batch_size=32,  # Prevent OOM
            #                                 show_progress_bar=False,
            #                                 normalize_embeddings=True
            #                             )

            transcript_embeddings = self.model.encode(
                transcript_texts,
                convert_to_tensor=True,
            )
                
           # Calculate similarities safely
            # similarities = util.cos_sim(query_embedding, self._cache[cache_key])[0].cpu().numpy()

            similarities = util.cos_sim(query_embedding, transcript_embeddings)[0].cpu().numpy()

            
            # Handle NaN/Inf values
            similarities = np.nan_to_num(similarities, nan=0.0)
            
            # Get valid sorted indices
            valid_indices = np.argsort(similarities)[::-1]
            valid_indices = valid_indices[:top_k]  # Prevent step error
            
            # Build results matching BasicSearch format
            results = []
            for idx in valid_indices:
                if idx < len(transcript):  # Prevent index errors
                    item = transcript[idx]
                    results.append({
                        "seconds": timestamps[idx],
                        "time": self.seconds_to_video_time(timestamps[idx]),
                        "text": transcript_texts[idx],
                        "video_link": f"{video_url}#t={int(timestamps[idx])}s",
                        "confidence": round(float(similarities[idx]), 3)
                    })

            return results

        except Exception as e:
            print(f"Error in SemanticSearch: {e}")