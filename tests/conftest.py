import pytest
from unittest.mock import Mock
from app.mongoDb.connection import MongoDBClient
from app.mongoDb.repository import VideoRepository
from app.services.video.video_service import VideoService


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client for testing."""
    return Mock(spec=MongoDBClient)


@pytest.fixture
def mock_video_repository(mock_mongo_client):
    """Mock video repository for testing."""
    mock_repo = Mock(spec=VideoRepository)
    return mock_repo


@pytest.fixture
def mock_video_service(mock_video_repository):
    """Mock video service for testing."""
    mock_storage_service = Mock()
    service = VideoService(mock_video_repository, storage_service=mock_storage_service)
    return service


@pytest.fixture
def sample_video_data():
    """Sample video data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "submission_id": "sub_test",
        "name": "Test Video",
        "category": "Test",
        "description": "Test description",
        "url": "https://example.com/video.mp4",
        "file_id": "test-file-id",
        "storage_type": "r2",
        "status": "completed",
        "transcript": [
            {"timestamp": 0, "text": "Hello world"},
            {"timestamp": 5, "text": "This is a test"}
        ]
    }


@pytest.fixture
def sample_video_create():
    """Sample video create data."""
    from app.schemas.video_schemas import VideoUploadRequest
    return VideoUploadRequest(
        submission_id="sub_test_upload",
        file_id="test-file-id",
        name="Test Video",
        category="Test",
        description="Test description"
    )
