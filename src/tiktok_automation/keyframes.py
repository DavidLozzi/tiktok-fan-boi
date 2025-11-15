from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np


class KeyframeExtractor:
    def __init__(self, max_frames: int, frames_path: Path, logger: logging.Logger):
        self.max_frames = min(max_frames, 50)
        self.frames_path = frames_path
        self.logger = logger
        self.frames_path.mkdir(parents=True, exist_ok=True)

    def extract(self, video_path: Path) -> List[str]:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            self.logger.error("Unable to open video for keyframes: %s", video_path)
            return []
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)
        step = max(frame_count // self.max_frames, 1)
        keyframes: List[str] = []
        index = 0
        while len(keyframes) < self.max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            success, frame = cap.read()
            if not success:
                break
            encoded = self._frame_to_base64(frame)
            keyframes.append(encoded)
            index += step
        cap.release()
        self.logger.debug("Extracted %s keyframes from %s", len(keyframes), video_path)
        return keyframes

    def _frame_to_base64(self, frame: np.ndarray) -> str:
        success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not success:
            raise RuntimeError("Failed to encode frame to JPEG")
        return base64.b64encode(buffer.tobytes()).decode("ascii")

