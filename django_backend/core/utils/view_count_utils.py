from core.models.f_etl_types import ETLTrack as Track
from core.models.f_etl_types import HistoricalView
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.config import CURRENT_TIMESTAMP
from core.utils.track_utils import get_delta_view_count
from core.utils.utils import get_logger
from core.utils.webdriver import get_cached_webdriver

logger = get_logger(__name__)


def update_spotify_track_view_count(track: Track) -> bool:
    if not track.spotify_track_data.track_url:
        return False

    webdriver = get_cached_webdriver()

    if track.spotify_view.start_view.timestamp is None:
        view_count = _get_spotify_view_count(webdriver, track.spotify_track_data.track_url)
        if view_count is None:
            return False
        track.spotify_view.start_view.view_count = view_count
        track.spotify_view.start_view.timestamp = CURRENT_TIMESTAMP

    view_count = _get_spotify_view_count(webdriver, track.spotify_track_data.track_url)
    if view_count is None:
        return False

    track.spotify_view.current_view.view_count = view_count
    track.spotify_view.current_view.timestamp = CURRENT_TIMESTAMP

    _update_spotify_historical_view(track, view_count)
    return True


def update_youtube_track_view_count(track: Track) -> bool:
    if not track.youtube_url:
        return False

    if track.youtube_view.start_view.timestamp is None:
        view_count = _get_youtube_view_count(track.youtube_url)
        if view_count is None:
            return False
        track.youtube_view.start_view.view_count = view_count
        track.youtube_view.start_view.timestamp = CURRENT_TIMESTAMP

    view_count = _get_youtube_view_count(track.youtube_url)
    if view_count is None:
        return False

    track.youtube_view.current_view.view_count = view_count
    track.youtube_view.current_view.timestamp = CURRENT_TIMESTAMP

    _update_youtube_historical_view(track, view_count)
    return True


def _get_spotify_view_count(webdriver, track_url: str) -> int | None:
    try:
        return webdriver.get_spotify_track_view_count(track_url)
    except Exception as e:
        logger.error(f"Error getting Spotify view count for {track_url}: {e}")
        return None


def _get_youtube_view_count(youtube_url: str) -> int | None:
    try:
        return get_youtube_track_view_count(youtube_url)
    except Exception as e:
        logger.error(f"Error getting Youtube view count for {youtube_url}: {e}")
        return None


def _update_spotify_historical_view(track: Track, current_view_count: int) -> None:
    if current_view_count is None:
        return

    historical_view = HistoricalView()
    historical_view.total_view_count = current_view_count
    delta_view_count = get_delta_view_count(
        track.spotify_view.historical_view,
        current_view_count,
    )
    historical_view.delta_view_count = delta_view_count
    historical_view.timestamp = CURRENT_TIMESTAMP
    track.spotify_view.historical_view.append(historical_view)


def _update_youtube_historical_view(track: Track, current_view_count: int) -> None:
    if current_view_count is None:
        return

    historical_view = HistoricalView()
    historical_view.total_view_count = current_view_count
    delta_view_count = get_delta_view_count(
        track.youtube_view.historical_view,
        current_view_count,
    )
    historical_view.delta_view_count = delta_view_count
    historical_view.timestamp = CURRENT_TIMESTAMP
    track.youtube_view.historical_view.append(historical_view)
