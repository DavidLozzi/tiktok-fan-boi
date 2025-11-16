from datetime import datetime
from pathlib import Path

from tiktok_automation.config import HistorySettings
from tiktok_automation.history import ProcessedHistory
from tiktok_automation.types import VideoArtifact, VideoMetadata


def make_artifact(tmp_path: Path) -> VideoArtifact:
    video_file = tmp_path / "video.mp4"
    video_file.write_bytes(b"binary")
    metadata = VideoMetadata(
        video_id="abc123",
        source_username="tester",
        canonical_url="https://www.tiktok.com/@tester/video/abc123",
        download_url="https://example.com/video.mp4",
        caption="hello",
        hashtags=["hello"],
    )
    return VideoArtifact(metadata=metadata, file_path=video_file, checksum="checksum")


def test_history_records_and_detects_duplicates(tmp_path):
    history_path = tmp_path / "history.jsonl"
    settings = HistorySettings(path=history_path, max_bytes=1024 * 1024, keep_rotations=2)
    history = ProcessedHistory(settings)
    artifact = make_artifact(tmp_path)

    assert not history.is_duplicate(artifact.metadata.video_id, artifact.metadata.canonical_url)
    history.record(artifact, status="uploaded", uploaded_at=datetime.utcnow())
    assert history.is_duplicate(artifact.metadata.video_id, artifact.metadata.canonical_url)
