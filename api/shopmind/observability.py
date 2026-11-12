"""Structured logs for each turn. Optional LangSmith export is env-driven."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("shopmind")


class TraceLog:
    def __init__(self) -> None:
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

    def emit(self, event: str, **fields: Any) -> None:
        payload = {"ts": datetime.now(UTC).isoformat(), "event": event, **fields}
        logger.info(json.dumps(payload, ensure_ascii=False, default=str))
