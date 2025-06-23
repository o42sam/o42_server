# tests/services/test_face_verification.py

import pytest
from pytest_mock import MockerFixture
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_create_face_mapping_from_video(mocker: MockerFixture):
    # Mock the lower-level face_recognition library functions
    fake_encoding = [[0.1, 0.2, 0.3]]
    mocker.patch("face_recognition.face_encodings", return_value=fake_encoding)
    mocker.patch("face_recognition.face_locations", return_value=[(0, 100, 100, 0)])
    mocker.patch("cv2.VideoCapture")

    # Create a mock file object
    mock_video_file = AsyncMock()
    mock_video_file.read.return_value = b"fakevideodata"
    mock_video_file.filename = "video.mp4"

    from app.services import face_verification
    result = await face_verification.create_face_mapping_from_video(mock_video_file)

    assert result == fake_encoding[0]