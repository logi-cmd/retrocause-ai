from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import TypeVar

from retrocause.api.runtime import run_with_timeout

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LiveAnalysisQueueTimeout(Exception):
    pass


_LIVE_ANALYSIS_SEMAPHORE = threading.BoundedSemaphore(
    max(1, int(os.environ.get("RETROCAUSE_LIVE_MAX_CONCURRENT", "1")))
)


def _live_queue_wait_seconds(timeout_seconds: float) -> float:
    configured = os.environ.get("RETROCAUSE_LIVE_QUEUE_WAIT_SECONDS")
    if configured:
        return max(0.0, float(configured))
    return timeout_seconds


def run_live_analysis_with_gate(
    fn: Callable[..., T],
    timeout_seconds: float,
    *args,
    **kwargs,
) -> T | None:
    """Serialize full live analysis calls inside the local OSS process."""

    queue_wait_seconds = _live_queue_wait_seconds(timeout_seconds)
    acquired = _LIVE_ANALYSIS_SEMAPHORE.acquire(timeout=queue_wait_seconds)
    if not acquired:
        raise LiveAnalysisQueueTimeout(
            "Another live analysis is already running. Wait for it to finish, then retry."
        )

    def guarded_call() -> T:
        try:
            return fn(*args, **kwargs)
        finally:
            _LIVE_ANALYSIS_SEMAPHORE.release()
            logger.info("Released local live-analysis gate")

    return run_with_timeout(guarded_call, timeout_seconds)
