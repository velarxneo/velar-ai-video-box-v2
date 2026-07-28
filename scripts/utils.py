"""Shared helpers for Velar bootstrap scripts."""

from __future__ import annotations

import logging
import os
from pathlib import Path


def env_path(name: str, default: str) -> Path:
    """Resolve an environment variable to an absolute Path, falling back to default."""
    return Path(os.environ.get(name, default)).expanduser().resolve()


def env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def configure_logging() -> None:
    level_name = os.environ.get("VELAR_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
