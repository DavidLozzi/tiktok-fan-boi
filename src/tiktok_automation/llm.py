from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import LLMSettings
from .types import CaptionResult, VideoMetadata


class LLMCaptioner:
    def __init__(self, settings: LLMSettings, logger: logging.Logger, client: Optional[OpenAI] = None):
        if settings.provider.lower() != "openai":
            raise ValueError("Only OpenAI provider is supported currently.")
        self.settings = settings
        self.logger = logger
        self.client = client or OpenAI()

    def generate(self, metadata: VideoMetadata, keyframes: List[str]) -> CaptionResult:
        fallback_caption = metadata.caption or metadata.extra.get("video_title") or "New upload"
        fallback_tags = metadata.hashtags[: self.settings.max_hashtags]
        try:
            caption, hashtags = self._invoke_llm(metadata, keyframes)
        except Exception as exc:  # pragma: no cover - network
            self.logger.error("LLM caption generation failed: %s", exc)
            caption, hashtags = fallback_caption, fallback_tags
        final_caption, credit_added = self._render_caption(
            caption, hashtags, metadata.source_username
        )
        return CaptionResult(
            caption=caption, hashtags=hashtags, final_caption=final_caption, credit_added=credit_added
        )

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _invoke_llm(self, metadata: VideoMetadata, keyframes: List[str]) -> Tuple[str, List[str]]:
        prompt = self._build_prompt(metadata)
        user_content = [{"type": "text", "text": prompt}]
        for frame in keyframes[:50]:
            user_content.append({"type": "input_image", "image_base64": frame})
        response = self.client.responses.create(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_output_tokens=self.settings.max_tokens,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are an assistant that writes concise, family-friendly TikTok captions. "
                                "Always respond with strict JSON: {\"caption\": str, \"hashtags\": [str]}. "
                                "Hashtags must not include # symbols."
                            ),
                        }
                    ],
                },
                {"role": "user", "content": user_content},
            ],
        )
        text_blocks = []
        for item in response.output:
            for content in item.content:
                if content.type == "output_text":
                    text_blocks.append(content.text)
        raw_text = "\n".join(text_blocks).strip()
        parsed = json.loads(raw_text)
        caption = parsed.get("caption", "").strip()
        hashtags = [h.strip().lstrip("#") for h in parsed.get("hashtags", []) if h.strip()]
        hashtags = self._normalize_hashtags(hashtags)
        return caption, hashtags

    def _build_prompt(self, metadata: VideoMetadata) -> str:
        music_line = ""
        if metadata.music_title or metadata.music_author:
            music_line = f"Music: {metadata.music_title or ''} by {metadata.music_author or ''}".strip()
        hashtag_line = ", ".join(f"#{tag}" for tag in metadata.hashtags) if metadata.hashtags else "None"
        return (
            "Create a short TikTok caption grounded in the provided frames and metadata.\n"
            f"Original Caption: {metadata.caption or 'N/A'}\n"
            f"Existing Hashtags: {hashtag_line}\n"
            f"{music_line}\n"
            f"Source handle: @{metadata.source_username}\n"
            f"Max hashtags: {self.settings.max_hashtags}\n"
            "Respond with JSON only."
        )

    def _normalize_hashtags(self, hashtags: List[str]) -> List[str]:
        deduped = []
        seen = set()
        for tag in hashtags:
            clean = tag.replace("#", "").strip().lower()
            if not clean or clean in seen:
                continue
            deduped.append(clean)
            seen.add(clean)
            if len(deduped) >= self.settings.max_hashtags:
                break
        return deduped

    def _render_caption(
        self, caption: str, hashtags: List[str], source_handle: str
    ) -> Tuple[str, bool]:
        caption = caption.strip() or "New upload"
        credit_line = f"Credit: @{source_handle}" if source_handle else ""
        credit_added = False
        caption_lower = caption.lower()
        credit_lower = credit_line.lower()
        if credit_line and credit_lower not in caption_lower:
            body = f"{caption}\n{credit_line}"
            credit_added = True
        else:
            body = caption
        hashtags = self._normalize_hashtags(hashtags)
        hashtag_line = " ".join(f"#{tag}" for tag in hashtags)
        if hashtag_line:
            final = f"{body}\n\n{hashtag_line}"
        else:
            final = body
        return final.strip(), credit_added

