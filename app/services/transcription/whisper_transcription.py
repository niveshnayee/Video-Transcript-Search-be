import whisper
from typing import List
from app.models.video_models import TranscriptSegment
from app.services.transcription.transcription_service import TranscriptionService

MODEL_SIZE="base"

class WhisperTranscriptionService(TranscriptionService):
     def __init__(self):
        self.model = whisper.load_model(MODEL_SIZE)

    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        result = self.model.transcribe(audio_path, word_timestamps=False)
        return [
            TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip()
            ) for seg in result["segments"]
        ]

    def format_transcript(self, segments: List[TranscriptSegment]) -> dict:
        return {
            "service": "whisper",
            "segments": [seg.dict() for seg in segments],
            "version": MODEL_SIZE
        }