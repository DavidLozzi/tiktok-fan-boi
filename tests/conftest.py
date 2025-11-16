import logging
from datetime import datetime

import pytest

from tiktok_automation.types import VideoMetadata


@pytest.fixture
def test_logger():
    logger = logging.getLogger("tiktok_automation_test")
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture
def sample_metadata():
    return VideoMetadata(
        video_id="123",
        source_username="source",
        canonical_url="https://www.tiktok.com/@source/video/123",
        download_url="https://example.com/video.mp4",
        caption="Original caption #fun",
        hashtags=["fun"],
        music_title="Song",
        music_author="Artist",
        created_at=datetime.utcnow(),
        extra={"video_title": "Sample video"},
    )

