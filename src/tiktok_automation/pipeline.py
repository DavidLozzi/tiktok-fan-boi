from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List

from .config import AppConfig
from .downloader import TikTokDownloader
from .history import ProcessedHistory
from .keyframes import KeyframeExtractor
from .llm import LLMCaptioner
from .types import VideoArtifact, VideoMetadata
from .uploader import TikTokUploader


class TikTokAutomationService:
    def __init__(self, config: AppConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.downloader = TikTokDownloader(config.download, logger)
        self.history = ProcessedHistory(config.history)
        self.keyframes = KeyframeExtractor(50, config.storage.frames_path, logger)
        self.captioner = LLMCaptioner(config.llm, logger)
        self.uploader = TikTokUploader(config.upload, logger)

    def run(self) -> None:
        candidates = self._collect_candidates()
        if not candidates:
            self.logger.info("No new videos to process.")
            return
        self.logger.info("Processing %s videos", len(candidates))
        with ThreadPoolExecutor(max_workers=self.config.download.concurrent_downloads) as pool:
            futures = {pool.submit(self._process_video, meta): meta for meta in candidates}
            for future in as_completed(futures):
                meta = futures[future]
                try:
                    future.result()
                except Exception as exc:  # pragma: no cover - concurrency
                    self.logger.error("Failed to process %s: %s", meta.video_id, exc)

    def _collect_candidates(self) -> List[VideoMetadata]:
        new_videos: List[VideoMetadata] = []
        seen = set()
        for username in self.config.download.usernames:
            try:
                videos = self.downloader.fetch_recent_metadata(username)
            except Exception as exc:
                self.logger.error("Failed to fetch metadata for %s: %s", username, exc)
                continue
            for video in videos:
                if self.history.is_duplicate(video.video_id, video.canonical_url):
                    self.logger.debug("Skipping duplicate %s", video.video_id)
                    continue
                if video.video_id in seen:
                    continue
                seen.add(video.video_id)
                new_videos.append(video)
        return new_videos

    def _process_video(self, metadata: VideoMetadata) -> None:
        artifact = self.downloader.download(metadata)
        try:
            artifact.keyframes = self.keyframes.extract(artifact.file_path)
        except Exception as exc:
            self.logger.warning("Keyframe extraction failed for %s: %s", metadata.video_id, exc)
            artifact.keyframes = []
        caption = self.captioner.generate(metadata, artifact.keyframes)
        try:
            self.uploader.upload(artifact.file_path, caption.final_caption)
            self.history.record(artifact, status="uploaded", uploaded_at=datetime.utcnow())
        except Exception as exc:
            self.logger.error("Upload failed for %s: %s", metadata.video_id, exc)
            self.history.record(artifact, status="upload_failed", uploaded_at=None)

