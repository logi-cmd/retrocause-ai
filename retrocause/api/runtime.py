import logging
import threading
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TimeoutError(Exception):
    pass


def run_with_timeout(
    fn: Callable[..., T],
    timeout_seconds: float,
    *args,
    **kwargs,
) -> T | None:
    result_box: list[T] = []
    exc_box: list[Exception] = []

    started_at = time.time()

    def target() -> None:
        try:
            logger.info(f"[TIMEOUT-DEBUG] target thread starting fn={fn.__name__!r}")
            result_box.append(fn(*args, **kwargs))
            logger.info(
                f"[TIMEOUT-DEBUG] target thread finished in {time.time() - started_at:.1f}s"
            )
        except Exception as exc:
            logger.error(f"[TIMEOUT-DEBUG] target thread caught {type(exc).__name__}: {exc}")
            exc_box.append(exc)

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(timeout=timeout_seconds)

    elapsed = time.time() - started_at
    logger.info(
        f"[TIMEOUT-DEBUG] thread join returned after {elapsed:.1f}s, "
        f"is_alive={worker.is_alive()}, result_box={len(result_box)}, exc_box={len(exc_box)}"
    )

    if worker.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s")

    if exc_box:
        raise exc_box[0]
    return result_box[0] if result_box else None
