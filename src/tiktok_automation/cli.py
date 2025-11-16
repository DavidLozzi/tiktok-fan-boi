from __future__ import annotations

from pathlib import Path

import typer
import yaml

from .config import load_config
from .logging_utils import configure_logging
from .pipeline import TikTokAutomationService

app = typer.Typer(help="TikTok video downloader and uploader CLI.")


CONFIG_TEMPLATE = {
    "download": {
        "usernames": ["tiktok"],
        "max_videos_per_user": 2,
        "concurrent_downloads": 3,
        "watermark_free": True,
        "request_timeout": 30,
        "storage_path": "data/downloads",
    },
    "upload": {
        "destination_account_id": None,
        "privacy": "public",
        "callback_url": None,
        "chunk_size_mb": 32,
        "retry": {"max_attempts": 5, "backoff_seconds": 3},
    },
    "llm": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_hashtags": 12,
        "max_tokens": 600,
    },
    "history": {
        "path": "data/processed_videos.jsonl",
        "max_bytes": 10485760,
        "keep_rotations": 5,
    },
    "logging": {
        "path": "logs/app.log",
        "level": "INFO",
        "max_bytes": 5242880,
        "backup_count": 3,
    },
    "storage": {
        "temp_path": "tmp",
        "frames_path": "tmp/frames",
    },
}


@app.command()
def init_config(path: Path = typer.Option(Path("config.yaml"), "--path", "-p"), force: bool = False) -> None:
    """Create a starter configuration file."""
    if path.exists() and not force:
        typer.echo(f"{path} already exists. Use --force to overwrite.")
        raise typer.Exit(code=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        yaml.safe_dump(CONFIG_TEMPLATE, fp, sort_keys=False)
    typer.echo(f"Wrote template config to {path}")


@app.command()
def sync(
    config_path: Path = typer.Option(Path("config.yaml"), "--config", "-c"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose console logs"),
) -> None:
    """Download recent TikToks, generate captions, and upload them."""
    config = load_config(config_path)
    logger = configure_logging(config.logging, verbose=verbose)
    service = TikTokAutomationService(config, logger)
    service.run()


def main() -> None:
    app()


if __name__ == "__main__":
    main()

