from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import DownloadSettings
from .types import VideoArtifact, VideoMetadata
from .utils import sha256_file

try:
    from TikTokApi import TikTokApi
except ImportError:  # pragma: no cover - dependency optional at runtime
    TikTokApi = None


HASHTAG_PATTERN = re.compile(r"#(\w+)")


class TikTokDownloader:
    def __init__(self, settings: DownloadSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            }
        )

    def fetch_recent_metadata(self, username: str) -> List[VideoMetadata]:
        if TikTokApi is None:
            raise RuntimeError(
                "TikTokApi is not installed. Install it via `pip install TikTokApi`."
            )
        videos: List[VideoMetadata] = []
        with TikTokApi() as api:
            user = api.user(username=username)
            tiktoks = user.videos(count=self.settings.max_videos_per_user)
            for raw in tiktoks:
                data = raw.as_dict
                video_id = data.get("id") or raw.id
                download_url = self._select_download_url(data)
                if not download_url:
                    self.logger.warning(
                        "Skipping video %s due to missing download URL", video_id
                    )
                    continue
                canonical = f"https://www.tiktok.com/@{username}/video/{video_id}"
                caption = data.get("desc", "")
                hashtags = self._extract_hashtags(caption)
                music = data.get("music", {})
                music_title = music.get("title") or music.get("originalSoundInfo", {}).get(
                    "originalSoundTitle"
                )
                music_author = music.get("authorName") or music.get("author", {}).get("nickname")
                create_time = data.get("createTime")
                created_at = (
                    datetime.fromtimestamp(create_time) if isinstance(create_time, (int, float)) else None
                )
                videos.append(
                    VideoMetadata(
                        video_id=str(video_id),
                        source_username=username,
                        canonical_url=canonical,
                        download_url=download_url,
                        caption=caption or "",
                        hashtags=hashtags,
                        music_title=music_title,
                        music_author=music_author,
                        created_at=created_at,
                        extra={"video_cover": data.get("video", {}).get("cover")},
                    )
                )
        return videos

    def download(self, metadata: VideoMetadata) -> VideoArtifact:
        file_path = self.settings.storage_path / f"{metadata.video_id}.mp4"
        payload = self._download_bytes(metadata.download_url)
        file_path.write_bytes(payload)
        checksum = sha256_file(file_path)
        self.logger.info(
            "Downloaded %s (%s bytes)", metadata.video_id, len(payload)
        )
        return VideoArtifact(metadata=metadata, file_path=file_path, checksum=checksum)

    def _select_download_url(self, data: dict) -> Optional[str]:
        video_info = data.get("video") or {}
        no_watermark = video_info.get("playAddr", "")
        watermark = video_info.get("downloadAddr", "")
        if self.settings.watermark_free and no_watermark:
            return no_watermark
        return watermark or no_watermark

    def _extract_hashtags(self, caption: str) -> List[str]:
        return sorted({match.lower() for match in HASHTAG_PATTERN.findall(caption or "")})

    @retry(
        retry=retry_if_exception_type((requests.RequestException, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _download_bytes(self, url: str) -> bytes:
        response = self.session.get(url, timeout=self.settings.request_timeout)
        response.raise_for_status()
        return response.content

