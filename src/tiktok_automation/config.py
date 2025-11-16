from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, validator


class RetrySettings(BaseModel):
    max_attempts: int = Field(3, ge=1, description="Maximum retry attempts")
    backoff_seconds: float = Field(
        2.0, ge=0, description="Base backoff in seconds for exponential retries"
    )


class DownloadSettings(BaseModel):
    usernames: List[str] = Field(..., min_items=1)
    max_videos_per_user: int = Field(1, ge=1, le=20)
    concurrent_downloads: int = Field(3, ge=1, le=16)
    watermark_free: bool = True
    request_timeout: float = Field(30.0, gt=0)
    storage_path: Path = Field(Path("data/downloads"))


class UploadSettings(BaseModel):
    destination_account_id: Optional[str] = Field(
        None, description="TikTok Business account ID used for uploads"
    )
    privacy: str = Field("public", regex="^(public|friends|private)$")
    callback_url: Optional[str] = None
    chunk_size_mb: int = Field(32, ge=8, le=128)
    retry: RetrySettings = RetrySettings()


class LLMSettings(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = Field(0.7, ge=0, le=2)
    max_hashtags: int = Field(12, ge=1, le=50)
    max_tokens: int = Field(600, ge=256, le=2000)
    retry: RetrySettings = RetrySettings(max_attempts=4, backoff_seconds=3.0)


class HistorySettings(BaseModel):
    path: Path = Path("data/processed_videos.jsonl")
    max_bytes: int = Field(10 * 1024 * 1024, ge=1024)
    keep_rotations: int = Field(5, ge=1, le=20)


class LoggingSettings(BaseModel):
    path: Path = Path("logs/app.log")
    level: str = Field("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    max_bytes: int = Field(5 * 1024 * 1024, ge=1024)
    backup_count: int = Field(3, ge=1, le=10)
    verbose: bool = False


class StorageSettings(BaseModel):
    temp_path: Path = Path("tmp")
    frames_path: Path = Path("tmp/frames")


class AppConfig(BaseModel):
    download: DownloadSettings
    upload: UploadSettings
    llm: LLMSettings = LLMSettings()
    history: HistorySettings = HistorySettings()
    logging: LoggingSettings = LoggingSettings()
    storage: StorageSettings = StorageSettings()

    @validator("download", "upload", "history", "logging", "storage", pre=True)
    def _expand_paths(cls, value):
        if isinstance(value, dict):
            for key, val in list(value.items()):
                if key.endswith("_path") or key == "path":
                    value[key] = Path(val)
        return value

    def ensure_directories(self) -> None:
        paths = [
            self.download.storage_path,
            self.storage.temp_path,
            self.storage.frames_path,
            self.logging.path.parent,
            self.history.path.parent,
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fp:
        if path.suffix.lower() in {".yaml", ".yml"}:
            raw = yaml.safe_load(fp)
        else:
            raw = yaml.safe_load(fp.read())

    config = AppConfig(**raw)
    config.ensure_directories()
    return config

