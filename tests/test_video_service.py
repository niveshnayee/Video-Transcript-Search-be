import pytest
from unittest.mock import Mock
from app.services.video.video_service import VideoService
from app.exceptions import VideoNotFoundException
from app.constants import VideoStatus
from app.schemas.video_schemas import SearchQuery


class TestVideoService:
    def test_get_all_videos(self, mock_video_service, sample_video_data):
        """Test getting all videos."""
        mock_video_service.repository.get_all_videos.return_value = [sample_video_data]

        result = mock_video_service.get_all_videos()

        assert len(result) == 1
        assert result[0]["name"] == "Test Video"
        mock_video_service.repository.get_all_videos.assert_called_once()

    def test_get_video_success(self, mock_video_service, sample_video_data):
        """Test getting a video successfully."""
        mock_video_service.repository.get_video.return_value = sample_video_data

        valid_video_id = "507f1f77bcf86cd799439011"
        result = mock_video_service.get_video(valid_video_id)

        assert result["name"] == "Test Video"
        mock_video_service.repository.get_video.assert_called_once_with(valid_video_id)

    def test_get_video_not_found(self, mock_video_service):
        """Test getting a non-existent video."""
        mock_video_service.repository.get_video.return_value = None

        valid_video_id = "507f1f77bcf86cd799439011"
        with pytest.raises(VideoNotFoundException):
            mock_video_service.get_video(valid_video_id)

    def test_delete_video(self, mock_video_service, sample_video_data):
        """Test deleting a video."""
        mock_video_service.repository.get_video.return_value = sample_video_data
        mock_video_service.storage_service.delete_file.return_value = None

        valid_video_id = "507f1f77bcf86cd799439011"
        mock_video_service.delete_video(valid_video_id)

        mock_video_service.repository.get_video.assert_called_once_with(valid_video_id)
        mock_video_service.storage_service.delete_file.assert_called_once_with("test-file-id")
        mock_video_service.repository.delete_video.assert_called_once_with(valid_video_id)

    def test_upload_video(self, mock_video_service, sample_video_create):
        """Test uploading a video."""
        mock_video_service.repository.save_video.return_value = "new-video-id"

        result = mock_video_service.upload_video(sample_video_create)

        assert result == "new-video-id"
        mock_video_service.repository.save_video.assert_called_once()
        saved_video = mock_video_service.repository.save_video.call_args.args[0]
        assert saved_video["submission_id"] == "sub_test_upload"

    def test_upload_generates_submission_id(self, mock_video_service):
        """Test uploading a video generates a submission ID when one is not provided."""
        from app.schemas.video_schemas import VideoUploadRequest

        mock_video_service.repository.save_video.return_value = "new-video-id"
        request = VideoUploadRequest(file_id="test-file-id")

        result = mock_video_service.upload_video(request)

        assert result == "new-video-id"
        saved_video = mock_video_service.repository.save_video.call_args.args[0]
        assert saved_video["submission_id"].startswith("sub_")

    def test_extract_youtube_video_id_valid(self, mock_video_service):
        """Test extracting YouTube video ID from valid URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = mock_video_service._extract_youtube_video_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_extract_youtube_video_id_invalid(self, mock_video_service):
        """Test extracting YouTube video ID from invalid URL."""
        url = "https://example.com/video"
        result = mock_video_service._extract_youtube_video_id(url)
        assert result is None

    def test_search_transcript_basic(self, mock_video_service, sample_video_data):
        """Test transcript search using basic strategy."""
        mock_video_service.repository.get_video.return_value = sample_video_data
        query = SearchQuery(query="hello", strategy="basic")
        valid_video_id = "507f1f77bcf86cd799439011"

        result = mock_video_service.search_transcript(valid_video_id, query)

        assert result.total_results == 1
        assert result.results[0].text == "Hello world"
        assert result.results[0].timestamp == 0
