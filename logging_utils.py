"""Structured logging helpers."""
import json
import logging
import time
from typing import Any

from config import get_settings


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.latency_ms = round((time.perf_counter() - self.start) * 1000, 2)


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, get_settings().log_level.upper(), logging.INFO),
        format="%(message)s",
    )


def log_event(logger: logging.Logger, message: str, *, level: int = logging.INFO, **fields: Any) -> None:
    payload = {"message": message, **fields}
    logger.log(level, json.dumps(payload, default=str))
