from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import LoggingSettings


def configure_logging(settings: LoggingSettings, verbose: bool = False) -> logging.Logger:
    log_level = getattr(logging, settings.level.upper(), logging.INFO)
    logger = logging.getLogger("tiktok_automation")
    logger.setLevel(log_level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=settings.path,
        maxBytes=settings.max_bytes,
        backupCount=settings.backup_count,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if verbose or settings.verbose else log_level)
    logger.addHandler(console_handler)

    logger.debug("Logger configured at level %s", logging.getLevelName(logger.level))
    return logger

