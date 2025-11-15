from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import UploadSettings
from .utils import env_or_fail


class TikTokUploader:
    API_URL = "https://open.tiktokapis.com/v2/video/upload/"

    def __init__(self, settings: UploadSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.session = requests.Session()
        self.access_token = env_or_fail("TIKTOK_ACCESS_TOKEN")

    def upload(self, video_path: Path, caption: str) -> Dict[str, Any]:
        self.logger.info(
            "Uploading %s with privacy=%s", video_path.name, self.settings.privacy
        )
        response = self._post_video(video_path, caption)
        data = response.json()
        if response.status_code >= 300 or data.get("error", {}).get("code"):
            raise RuntimeError(f"TikTok upload failed: {data}")
        self.logger.info("Upload complete for %s", video_path.name)
        return data

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _post_video(self, video_path: Path, caption: str) -> requests.Response:
        files = {"video": (video_path.name, video_path.open("rb"), "video/mp4")}
        payload = {
            "privacy_level": self.settings.privacy,
            "text": caption,
        }
        if self.settings.destination_account_id:
            payload["account_id"] = self.settings.destination_account_id
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        response = self.session.post(
            self.API_URL,
            headers=headers,
            data=payload,
            files=files,
            timeout=120,
        )
        response.raise_for_status()
        return response

