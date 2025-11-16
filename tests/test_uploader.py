import responses

from tiktok_automation.config import UploadSettings
from tiktok_automation.uploader import TikTokUploader


@responses.activate
def test_uploader_posts_video(monkeypatch, tmp_path, test_logger):
    monkeypatch.setenv("TIKTOK_ACCESS_TOKEN", "tok")
    settings = UploadSettings(destination_account_id="acct", privacy="friends", chunk_size_mb=32, retry={"max_attempts": 1, "backoff_seconds": 1})
    uploader = TikTokUploader(settings, test_logger)
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"video")

    responses.add(
        responses.POST,
        TikTokUploader.API_URL,
        json={"data": {"video_id": "1"}},
        status=200,
    )

    result = uploader.upload(video_path, caption="caption")
    assert result["data"]["video_id"] == "1"
    assert responses.calls[0].request.headers["Authorization"] == "Bearer tok"
