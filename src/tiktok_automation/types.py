from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(slots=True)
class VideoMetadata:
    video_id: str
    source_username: str
    canonical_url: str
    download_url: str
    caption: str
    hashtags: List[str]
    music_title: Optional[str] = None
    music_author: Optional[str] = None
    created_at: Optional[datetime] = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class VideoArtifact:
    metadata: VideoMetadata
    file_path: Path
    checksum: str
    keyframes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class CaptionResult:
    caption: str
    hashtags: List[str]
    final_caption: str
    credit_added: bool

