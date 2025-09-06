import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from core.utils.utils import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_spotify_playlist_with_spotdl(playlist_url: str) -> JSON:
    """Fetch Spotify playlist data using SpotDL with retry logic for intermittent failures"""

    logger.info(f"Fetching Spotify playlist {playlist_url} using SpotDL")

    # Log SpotDL version for debugging
    try:
        version_result = subprocess.run(["spotdl", "--version"], capture_output=True, text=True, timeout=10)
        logger.info(f"SpotDL version: {version_result.stdout.strip()}")
    except Exception as e:
        logger.warning(f"Could not get SpotDL version: {e}")

    return _fetch_spotify_playlist_with_retry(playlist_url)


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _fetch_spotify_playlist_with_retry(playlist_url: str) -> JSON:
    """Internal function with retry decorator for SpotDL command execution"""
    # Create a temporary file with .spotdl extension
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".spotdl", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        cmd = ["spotdl", "save", playlist_url, "--save-file", temp_path, "--lyrics", "genius"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            error_msg = f"SpotDL failed with exit code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr}"
            if result.stdout:
                error_msg += f" | stdout: {result.stdout}"
            raise RuntimeError(error_msg)

        # Read the JSON from the temp file
        with open(temp_path) as f:
            spotdl_data = json.load(f)

        return spotdl_data

    finally:
        # Clean up the temp file
        Path(temp_path).unlink(missing_ok=True)
