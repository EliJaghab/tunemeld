import concurrent.futures
import logging
import os
import zoneinfo
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv


def to_et_format(timestamp: datetime | int | str) -> str:
    """
    Convert timestamp to Eastern Time format for less verbose and easier to read logs.

    Args:
        timestamp: datetime object, unix timestamp (int), or ISO string

    Returns:
        Formatted timestamp string in ET (MM/DD/YY H:MM:SSPM ET format)
    """
    if isinstance(timestamp, int):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = timestamp
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

    et_tz = zoneinfo.ZoneInfo("America/New_York")
    et_dt = dt.astimezone(et_tz)

    return et_dt.strftime("%m/%d/%y %I:%M:%S%p ET").replace(" 0", " ")


def get_logger(name: str) -> logging.Logger:
    """Setup and configure logger with slim ET format."""

    class ETFormatter(logging.Formatter):
        def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
            et_time = to_et_format(int(record.created))
            return et_time.split()[1] + " ET"

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(ETFormatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger(__name__)


def set_secrets() -> None:
    if not os.getenv("GITHUB_ACTIONS"):
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env.dev"))
        logger.info("env_path" + env_path)
        load_dotenv(dotenv_path=env_path)


def process_in_parallel(
    items: list[Any],
    process_func: Callable[[Any], Any],
    max_workers: int | None = None,
    log_progress: bool = True,
    progress_interval: int = 50,
) -> list[tuple[Any, Any | None, Exception | None]]:
    """
    Process items in parallel using ThreadPoolExecutor.

    Args:
        items: List of items to process
        process_func: Function to process each item
        max_workers: Maximum number of worker threads (default: min(len(items), 10))
        log_progress: Whether to log progress
        progress_interval: Log progress every N items

    Returns:
        List of tuples: (item, result, exception)
    """
    if not items:
        return []

    if max_workers is None:
        max_workers = min(len(items), 10)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(process_func, item): item for item in items}

        completed = 0
        total = len(items)

        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append((item, result, None))
                completed += 1

                if log_progress and completed % progress_interval == 0:
                    logger.info(f"Processed {completed}/{total} items")
            except Exception as exc:
                results.append((item, None, exc))
                logger.error(f"Failed to process item: {exc}")
                completed += 1

    if log_progress:
        logger.info(f"Completed processing {completed}/{total} items")

    return results
