from unittest.mock import Mock

import pytest

from app.constants import VideoStatus
from app.models.video_models import TranscriptSegment
from app.services.video import video_processing
from app.services.video.video_processing import VideoProcessingService


@pytest.fixture
def processing_dependencies():
    return {
        "video_utils": Mock(),
        "file_cleanup": Mock(),
        "transcription_service": Mock(),
        "video_repo": Mock(),
        "storage_service": Mock(),
    }


@pytest.fixture
def processing_service(processing_dependencies):
    return VideoProcessingService(**processing_dependencies)


def test_process_r2_video_success(processing_service, processing_dependencies):
    repo = processing_dependencies["video_repo"]
    storage = processing_dependencies["storage_service"]
    video_utils = processing_dependencies["video_utils"]
    transcription = processing_dependencies["transcription_service"]
    cleanup = processing_dependencies["file_cleanup"]

    repo.get_video.return_value = {
        "storage_type": "r2",
        "file_id": "sample.mp4",
    }
    video_utils.extract_audio.return_value = "/tmp/video_processing_video123/sample.wav"
    transcription.transcribe.return_value = [
        TranscriptSegment(start=1.2, end=2.8, text="Hello background job")
    ]

    result = processing_service.process_video("video123")

    assert result == {"video_id": "video123", "status": "success"}
    repo.update_status.assert_any_call("video123", VideoStatus.PROCESSING)
    repo.update_status.assert_any_call("video123", VideoStatus.COMPLETED)
    storage.download_file.assert_called_once()
    video_utils.extract_audio.assert_called_once()
    transcription.transcribe.assert_called_once()
    repo.add_transcript.assert_called_once()
    saved_transcript = repo.add_transcript.call_args.args[1]
    assert saved_transcript[0].timestamp == 1
    assert saved_transcript[0].text == "Hello background job"
    cleanup.cleanup_temp_files.assert_called_once()


def test_process_video_failure_marks_failed_and_cleans_up(processing_service, processing_dependencies):
    repo = processing_dependencies["video_repo"]
    video_utils = processing_dependencies["video_utils"]
    cleanup = processing_dependencies["file_cleanup"]

    repo.get_video.return_value = {
        "storage_type": "r2",
        "file_id": "sample.mp4",
    }
    video_utils.extract_audio.side_effect = RuntimeError("ffmpeg failed")

    with pytest.raises(RuntimeError, match="ffmpeg failed"):
        processing_service.process_video("video123")

    repo.update_status.assert_any_call("video123", VideoStatus.PROCESSING)
    repo.update_status.assert_any_call("video123", VideoStatus.FAILED)
    cleanup.cleanup_temp_files.assert_called_once()


def test_process_video_missing_metadata_marks_failed(processing_service, processing_dependencies):
    repo = processing_dependencies["video_repo"]

    repo.get_video.return_value = None

    with pytest.raises(Exception, match="Video metadata not found"):
        processing_service.process_video("missing-video")

    repo.update_status.assert_any_call("missing-video", VideoStatus.PROCESSING)
    repo.update_status.assert_any_call("missing-video", VideoStatus.FAILED)


def test_build_audio_path_uses_wav_extension(processing_service):
    assert processing_service.build_audio_path("/tmp/sample.mp4") == "/tmp/sample.wav"


def test_build_searchable_transcript(processing_service):
    transcript = processing_service.build_searchable_transcript(
        [TranscriptSegment(start=4.9, end=8.0, text="A transcript segment")]
    )

    assert transcript[0].timestamp == 4
    assert transcript[0].text == "A transcript segment"


def test_process_video_background_task_delegates_to_service(monkeypatch):
    service = Mock()
    service.process_video.return_value = {"video_id": "video123", "status": "success"}
    monkeypatch.setattr(video_processing, "create_video_processing_service", lambda: service)

    result = video_processing.process_video_background_task.run("video123")

    assert result == {"video_id": "video123", "status": "success"}
    service.process_video.assert_called_once_with("video123")
