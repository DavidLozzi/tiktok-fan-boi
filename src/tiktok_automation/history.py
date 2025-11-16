from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .config import HistorySettings
from .types import VideoArtifact
from .utils import append_jsonl_atomic


@dataclass(slots=True)
class HistoryEntry:
    video_id: str
    source_username: str
    canonical_url: str
    downloaded_at: str
    uploaded_at: Optional[str]
    status: str
    file_path: str
    checksum: str


class ProcessedHistory:
    def __init__(self, settings: HistorySettings):
        self.settings = settings
        self.index: Dict[str, HistoryEntry] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        path = self.settings.path
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                entry = HistoryEntry(**record)
                self.index[entry.video_id] = entry
                if entry.canonical_url:
                    self.index.setdefault(entry.canonical_url, entry)

    def is_duplicate(self, video_id: str, canonical_url: str) -> bool:
        return video_id in self.index or canonical_url in self.index

    def record(
        self,
        artifact: VideoArtifact,
        status: str,
        uploaded_at: Optional[datetime],
    ) -> HistoryEntry:
        entry = HistoryEntry(
            video_id=artifact.metadata.video_id,
            source_username=artifact.metadata.source_username,
            canonical_url=artifact.metadata.canonical_url,
            downloaded_at=datetime.utcnow().isoformat(),
            uploaded_at=uploaded_at.isoformat() if uploaded_at else None,
            status=status,
            file_path=str(artifact.file_path),
            checksum=artifact.checksum,
        )
        append_jsonl_atomic(self.settings.path, asdict(entry))
        self.index[entry.video_id] = entry
        if entry.canonical_url:
            self.index[entry.canonical_url] = entry
        self._rotate_if_needed()
        return entry

    def _rotate_if_needed(self) -> None:
        path = self.settings.path
        if not path.exists():
            return
        if path.stat().st_size <= self.settings.max_bytes:
            return
        for idx in range(self.settings.keep_rotations, 0, -1):
            older = Path(f"{path}.{idx}")
            if older.exists():
                if idx == self.settings.keep_rotations:
                    older.unlink()
                else:
                    target = Path(f"{path}.{idx + 1}")
                    older.replace(target)
        rotated = Path(f"{path}.1")
        shutil.move(path, rotated)

