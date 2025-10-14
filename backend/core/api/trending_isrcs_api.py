from collections import defaultdict

from core.api.response_utils import ResponseStatus, create_response
from core.constants import GenreName, ServiceName
from core.models.genre_service import GenreModel, ServiceModel
from core.models.playlist import PlaylistModel, RawPlaylistDataModel
from core.utils.redis_cache import SEVEN_DAYS_TTL, CachePrefix, redis_cache_get, redis_cache_set
from django.http import HttpRequest, JsonResponse


def get_trending_isrcs(request: HttpRequest) -> JsonResponse:
    """
    Endpoint for ReccoBeats integration.
    Returns weekly ISRC data from TuneMeld's 12 curator playlists organized by genre and service.
    """
    cache_key = "weekly_trending_isrcs"
    cached_data = redis_cache_get(CachePrefix.TRENDING_ISRCS, cache_key)

    if cached_data:
        return create_response(
            ResponseStatus.SUCCESS, "Weekly trending ISRCs from TuneMeld curator playlists (cached)", cached_data
        )

    trending_data = _build_trending_isrcs_response()
    redis_cache_set(CachePrefix.TRENDING_ISRCS, cache_key, trending_data, ttl=SEVEN_DAYS_TTL)

    return create_response(
        ResponseStatus.SUCCESS, "Weekly trending ISRCs from TuneMeld curator playlists", trending_data
    )


def _build_trending_isrcs_response() -> dict:
    """Build the full trending ISRCs response structure."""
    playlists_data = []
    all_isrcs: set[str] = set()
    genre_service_data: dict[tuple[str, str], dict] = defaultdict(lambda: {"isrcs": set(), "track_count": 0})

    for genre in GenreName:
        genre_obj = GenreModel.objects.filter(name=genre.value).first()
        if not genre_obj:
            continue

        for service in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD]:
            service_obj = ServiceModel.objects.filter(name=service.value).first()
            if not service_obj:
                continue

            raw_playlist = RawPlaylistDataModel.objects.filter(genre=genre_obj, service=service_obj).first()

            isrcs = list(
                PlaylistModel.objects.filter(genre=genre_obj, service=service_obj, isrc__isnull=False)
                .values_list("isrc", flat=True)
                .distinct()
            )

            playlist_entry = {
                "genre": genre.value,
                "service": service.value,
                "playlist_name": raw_playlist.playlist_name if raw_playlist else "",
                "playlist_url": raw_playlist.playlist_url if raw_playlist else "",
                "track_count": len(isrcs),
                "isrcs": isrcs,
            }

            playlists_data.append(playlist_entry)
            all_isrcs.update(isrcs)
            genre_service_data[(genre.value, service.value)] = {"isrcs": set(isrcs), "track_count": len(isrcs)}

    latest_raw_playlist = RawPlaylistDataModel.objects.order_by("-created_at").first()
    last_updated = latest_raw_playlist.created_at if latest_raw_playlist else None

    return {
        "metadata": {
            "total_isrcs": len(all_isrcs),
            "total_tracks": len(all_isrcs),
            "last_updated": last_updated.isoformat() if last_updated else None,
            "update_schedule": "Weekly on Saturday at 2:30 AM UTC",
            "genres": [genre.value for genre in GenreName],
            "services": [ServiceName.SPOTIFY.value, ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value],
        },
        "playlists": playlists_data,
        "all_isrcs": sorted(all_isrcs),
    }
