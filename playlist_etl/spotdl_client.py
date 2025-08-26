import json
import subprocess
from typing import Any

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_spotify_playlist_with_spotdl(playlist_url: str) -> JSON:
    """Fetch Spotify playlist data using SpotDL and convert to Spotify API format"""

    logger.info(f"Fetching Spotify playlist {playlist_url} using SpotDL")

    cmd = ["spotdl", "save", playlist_url, "--save-file", "-", "--lyrics", "genius"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        raise RuntimeError(f"SpotDL failed with exit code {result.returncode}: {result.stderr}")

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
