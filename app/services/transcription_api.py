
import whisper


class TranscriptionService:
    @staticmethod
    def transcribe_audio_with_timestamps(audio_path, model_size="base"):
        """Transcribe audio using Whisper and return segments with timestamps."""
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path, word_timestamps=False)  # Set word_timestamps=False for segment-level timestamps

        return get_transcription_with_minute_timestamps(result["segments"])

    @staticmethod
    def get_transcription_with_minute_timestamps(segments):
        """Group transcription into minute-wise timestamps."""
        transcript_items = []
        for segment in segments:
            start_time = int(segment["start"])
            text = segment["text"]

            # Create a TranscriptItem for each segment
            transcript_items.append({
                "timestamp": start_time,  # Store the timestamp
                "text": text  # Store the corresponding transcribed text
            })
            {
                # Group by minute
                # minute_key = f"{start_time // 60:02d}:{start_time % 60:02d}"
                # if minute_key not in minute_transcriptions:
                #     minute_transcriptions[minute_key] = []
                # minute_transcriptions[minute_key].append((start_time, end_time, text))
            }   
        return transcript_items

    @staticmethod
    def group_transcription_by_minutes(segments):
        """
        Group transcription into minute-wise spans while ensuring complete sentences.

        Args:
            segments (list): List of Whisper transcription segments.

        Returns:
            dict: Dictionary with minute spans as keys and combined text as values.
        """
        minute_transcriptions = {}
        current_text = ""
        current_start = 0
        last_end = 0
        minute_key = "00:00"

        for segment in segments:
            start_time = int(segment["start"])
            end_time = int(segment["end"])
            text = segment["text"]

            # If the current segment's start time exceeds the 1-minute boundary, finalize the current block
            if start_time // 60 != current_start // 60:
                # Finalize the previous minute block
                if current_text.strip():
                    minute_transcriptions[minute_key] = {
                        "start": current_start,
                        "end": last_end,
                        "text": current_text.strip(),
                    }

                # Start a new block
                current_start = start_time
                minute_key = f"{current_start // 60:02d}:00"
                current_text = ""

            # Append the current segment's text to the block
            current_text += " " + text
            last_end = end_time

        # Finalize the last block
        if current_text.strip():
            minute_transcriptions[minute_key] = {
                "start": current_start,
                "end": last_end,
                "text": current_text.strip(),
            }

        return minute_transcriptions

