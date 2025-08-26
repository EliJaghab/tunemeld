import json
import subprocess
from typing import Any

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_spotify_playlist_with_spotdl(playlist_url: str) -> JSON:
    """Fetch Spotify playlist data using SpotDL and convert to Spotify API format"""

    logger.info(f"Fetching Spotify playlist {playlist_url} using SpotDL")

    # Log SpotDL version for debugging
    try:
        version_result = subprocess.run(["spotdl", "--version"], capture_output=True, text=True, timeout=10)
        logger.info(f"SpotDL version: {version_result.stdout.strip()}")
    except Exception as e:
        logger.warning(f"Could not get SpotDL version: {e}")

    cmd = ["spotdl", "save", playlist_url, "--save-file", "-", "--lyrics", "genius"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        error_msg = f"SpotDL failed with exit code {result.returncode}"
        if result.stderr:
            error_msg += f": {result.stderr}"
        if result.stdout:
            error_msg += f" | stdout: {result.stdout}"
        raise RuntimeError(error_msg)

    # Parse the SpotDL JSON output from stdout
    # SpotDL outputs some logging to stdout before the JSON, so we need to extract just the JSON part
    stdout_lines = result.stdout.strip().split("\n")
    json_start_idx = -1

    # Find where the JSON array starts
    for i, line in enumerate(stdout_lines):
        if line.strip().startswith("["):
            json_start_idx = i
            break

    if json_start_idx == -1:
        raise RuntimeError(f"Could not find JSON array in SpotDL output: {result.stdout}")

    json_output = "\n".join(stdout_lines[json_start_idx:])

    try:
        spotdl_data = json.loads(json_output)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse SpotDL output as JSON: {e}") from e

    return spotdl_data
