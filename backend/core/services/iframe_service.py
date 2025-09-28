import re
from urllib.parse import quote

from core.constants import IFRAME_CONFIGS, ServiceName


def get_spotify_track_id(url: str) -> str:
    """Extract Spotify track/album/playlist ID from URL."""
    match = re.search(r"/(track|album|playlist)/([a-zA-Z0-9]+)", url)
    return f"{match.group(1)}/{match.group(2)}" if match else ""


def get_apple_music_id(url: str) -> str:
    """Extract Apple Music album ID from URL."""
    match = re.search(r"/album/[^/]+/(\d+)\?i=(\d+)", url)
    return f"{match.group(1)}?i={match.group(2)}" if match else ""


def get_youtube_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else ""


def generate_iframe_src(service_name: str, url: str) -> str:
    """Generate iframe src URL for a given service and track URL."""
    if service_name not in IFRAME_CONFIGS:
        raise ValueError(f"Unsupported service: {service_name}")

    config = IFRAME_CONFIGS[service_name]
    base_url = config["embed_base_url"]

    if service_name == ServiceName.SOUNDCLOUD:
        src = f"{base_url}?url={quote(url)}"
        if config.get("embed_params"):
            src += f"&{config['embed_params']}"
        return src

    elif service_name == ServiceName.SPOTIFY:
        track_id = get_spotify_track_id(url)
        return f"{base_url}{track_id}"

    elif service_name == ServiceName.APPLE_MUSIC:
        music_id = get_apple_music_id(url)
        return f"{base_url}{music_id}"

    elif service_name == ServiceName.YOUTUBE:
        video_id = get_youtube_video_id(url)
        src = f"{base_url}{video_id}"
        if config.get("embed_params"):
            src += f"?{config['embed_params']}"
        return src

    else:
        raise ValueError(f"Iframe generation not implemented for service: {service_name}")


def get_iframe_config(service_name: str) -> dict:
    """Get iframe configuration for a service."""
    if service_name not in IFRAME_CONFIGS:
        raise ValueError(f"Unsupported service: {service_name}")

    return IFRAME_CONFIGS[service_name]
