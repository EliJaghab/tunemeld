import logging
from enum import Enum

from django.conf import settings
from django.http import JsonResponse

print("[VIEWS] Loading Django views...")

# Safe cache import with fallback
try:
    from core.cache import Cache

    cache = Cache()
    print("[VIEWS] Cache initialized successfully")
except Exception as e:
    print(f"[VIEWS] Cache initialization failed: {e}")
    cache = None

# Safe MongoDB imports with fallback
try:
    from . import (
        historical_track_views,
        playlists_collection,
        raw_playlists_collection,
        transformed_playlists_collection,
    )

    print("[VIEWS] MongoDB collections imported successfully")
except Exception as e:
    print(f"[VIEWS] MongoDB import failed: {e}")
    historical_track_views = None
    playlists_collection = None
    raw_playlists_collection = None
    transformed_playlists_collection = None

logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"


def create_response(status: ResponseStatus, message: str, data=None):
    return JsonResponse({"status": status.value, "message": message, "data": data})


def root(request):
    """Root endpoint with extensive debugging"""
    print("\n=== ROOT ENDPOINT CALLED ===")
    print(f"🏠 Request method: {request.method}")
    print(f"📍 Request path: {request.path}")
    print(f"🌍 Request host: {request.get_host()}")
    print(f"📄 Request headers: {dict(request.headers)}")
    print(f"⚙️ Django settings DEBUG: {settings.DEBUG}")
    print(f"📍 Django ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print("=== END ROOT DEBUG ===\n")
    return create_response(ResponseStatus.SUCCESS, "Welcome to the TuneMeld Backend! Django is running.")


def health(request):
    """Health check endpoint for Railway deployment monitoring"""
    return create_response(ResponseStatus.SUCCESS, "Service is healthy")


def get_graph_data(request, genre_name):
    if playlists_collection is None:
        return create_response(ResponseStatus.ERROR, "Database not available", None)

    key = f"graph_data_{genre_name}"

    if cache:
        cached_response = cache.get(key)
        if cached_response:
            return create_response(
                ResponseStatus.SUCCESS, "Graph data retrieved successfully from cache", cached_response
            )

    try:

        def get_tracks_from_playlist(genre_name: str) -> list[dict]:
            playlists = playlists_collection.find({"genre_name": genre_name}, {"_id": False})
            tracks = [
                {
                    "isrc": track["isrc"],
                    "artist_name": track["artist_name"],
                    "youtube_url": track.get("youtube_url", ""),
                    "album_cover_url": track.get("album_cover_url", ""),
                }
                for track in playlists[0]["tracks"]
            ]
            return tracks

        def get_view_counts(isrc_list: list[str]) -> dict:
            track_views_query = {"isrc": {"$in": isrc_list}}
            track_views = historical_track_views.find(track_views_query)

            isrc_to_track_views = {}
            for track in track_views:
                isrc_to_track_views[track["isrc"]] = track
            return isrc_to_track_views

        tracks = get_tracks_from_playlist(genre_name)
        isrc_list = [track["isrc"] for track in tracks]
        track_views = get_view_counts(isrc_list)
        for track in tracks:
            if track["isrc"] in track_views and "view_counts" in track_views[track["isrc"]]:
                for service_name, view_counts in track_views[track["isrc"]]["view_counts"].items():
                    track["view_counts"] = track.get("view_counts", {})
                    track["view_counts"][service_name] = [
                        [
                            view["current_timestamp"],
                            view["delta_count"],
                        ]
                        for view in view_counts
                    ]
        cache.put(key, tracks)
        return create_response(ResponseStatus.SUCCESS, "Graph data retrieved successfully", tracks)

    except Exception as error:
        logger.exception("Error in get_graph_data view")
        return create_response(ResponseStatus.ERROR, str(error), None)


def get_playlist_data(request, genre_name):
    if playlists_collection is None:
        return create_response(ResponseStatus.ERROR, "Database not available", None)

    try:
        data = list(playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return create_response(ResponseStatus.ERROR, "No data found for the specified genre", None)
        return create_response(ResponseStatus.SUCCESS, "Playlist data retrieved successfully", data)
    except Exception as error:
        return create_response(ResponseStatus.ERROR, str(error), None)


def get_service_playlist(request, genre_name, service_name):
    if transformed_playlists_collection is None:
        return create_response(ResponseStatus.ERROR, "Database not available", None)

    try:
        data = list(
            transformed_playlists_collection.find(
                {"genre_name": genre_name, "service_name": service_name}, {"_id": False}
            )
        )
        if not data:
            return create_response(ResponseStatus.ERROR, "No data found for the specified genre and service", None)
        return create_response(ResponseStatus.SUCCESS, "Service playlist data retrieved successfully", data)
    except Exception as error:
        return create_response(ResponseStatus.ERROR, str(error), None)


def get_last_updated(request, genre_name):
    if playlists_collection is None:
        return create_response(ResponseStatus.ERROR, "Database not available", None)

    try:
        data = list(playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return create_response(ResponseStatus.ERROR, "No data found for the specified genre", None)

        last_updated = data[0]["insert_timestamp"]
        return create_response(
            ResponseStatus.SUCCESS,
            "Last updated timestamp retrieved successfully",
            {"last_updated": last_updated},
        )
    except Exception as error:
        return create_response(ResponseStatus.ERROR, str(error), None)


def get_header_art(request, genre_name):
    if raw_playlists_collection is None:
        return create_response(ResponseStatus.ERROR, "Database not available", None)

    try:
        data = list(raw_playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return create_response(ResponseStatus.ERROR, "No data found for the specified genre", None)

        formatted_data = format_playlist_data(data)
        return create_response(ResponseStatus.SUCCESS, "Header art data retrieved successfully", formatted_data)
    except Exception as error:
        return create_response(ResponseStatus.ERROR, str(error), None)


def format_playlist_data(data):
    result = {}
    for item in data:
        if item["service_name"] not in result:
            result[item["service_name"]] = {
                "playlist_cover_url": item.get("playlist_cover_url", ""),
                "playlist_cover_description_text": item.get("playlist_cover_description_text", ""),
                "playlist_name": item.get("playlist_name", ""),
                "playlist_url": item.get("playlist_url", ""),
            }
    return result
