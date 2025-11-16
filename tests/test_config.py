import yaml

from tiktok_automation.config import AppConfig, load_config


def test_load_config_creates_directories(tmp_path):
    config_path = tmp_path / "config.yaml"
    data = {
        "download": {
            "usernames": ["alpha"],
            "max_videos_per_user": 1,
            "concurrent_downloads": 1,
            "watermark_free": True,
            "request_timeout": 30,
            "storage_path": str(tmp_path / "downloads"),
        },
        "upload": {
            "destination_account_id": None,
            "privacy": "public",
            "callback_url": None,
            "chunk_size_mb": 32,
            "retry": {"max_attempts": 3, "backoff_seconds": 2},
        },
    }
    with config_path.open("w", encoding="utf-8") as fp:
        yaml.safe_dump(data, fp)

    config = load_config(config_path)
    assert isinstance(config, AppConfig)
    assert config.download.storage_path.exists()
