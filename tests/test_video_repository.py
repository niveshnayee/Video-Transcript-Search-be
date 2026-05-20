import pytest
from unittest.mock import Mock
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.exceptions import DuplicateSubmissionIdException
from app.mongoDb.repository import VideoRepository


def test_repository_creates_unique_submission_id_index():
    collection = Mock(spec=Collection)
    VideoRepository(collection)

    collection.create_index.assert_called_with(
        "submission_id",
        unique=True,
        sparse=True,
        name="unique_submission_id",
    )


def test_save_video_rejects_duplicate_submission_id():
    collection = Mock(spec=Collection)
    repository = VideoRepository(collection)
    collection.insert_one.side_effect = DuplicateKeyError("duplicate")

    with pytest.raises(DuplicateSubmissionIdException):
        repository.save_video({"submission_id": "sub_duplicate"})
