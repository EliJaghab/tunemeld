import os
from functools import lru_cache

from core.models.f_etl_types import HistoricalView
from core.utils.helpers import get_logger
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

logger = get_logger(__name__)


@lru_cache(maxsize=4)
def get_spotify_client(client_id: str | None = None, client_secret: str | None = None) -> Spotify:
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or client secret not provided.")
    return Spotify(
        client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    )


def get_delta_view_count(historical_views: list[HistoricalView], current_view_count: int) -> int:
    if not historical_views:
        return 0
    latest_view = historical_views[-1]
    return current_view_count - latest_view.total_view_count
