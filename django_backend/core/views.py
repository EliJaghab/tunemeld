import logging
from enum import Enum

from django.http import JsonResponse

from . import (
    historical_track_views,
    playlists_collection,
    raw_playlists_collection,
    transformed_playlists_collection,
)
from .cache import Cache

logger = logging.getLogger(__name__)

cache = Cache()




class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"


def create_response(status: ResponseStatus, message: str, data=None):
    return JsonResponse({"status": status.value, "message": message, "data": data})


def root(request):
    return create_response(ResponseStatus.SUCCESS, "Welcome to the TuneMeld Backend!")


def health(request):
    """Health check endpoint for Railway deployment monitoring"""
    return create_response(ResponseStatus.SUCCESS, "Service is healthy")


def get_graph_data(request, genre_name):
    key = f"graph_data_{genre_name}"

    cached_response = cache.get(key)
    if cached_response:
        return create_response(ResponseStatus.SUCCESS, "Graph data retrieved successfully from cache", cached_response)

    try:
        if not playlists_collection or not historical_track_views:
            return create_response(ResponseStatus.ERROR, "Database connection not available", None)

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
    try:
        if not playlists_collection:
            return create_response(ResponseStatus.ERROR, "Database connection not available", None)
        
        data = list(playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return create_response(ResponseStatus.ERROR, "No data found for the specified genre", None)
        return create_response(ResponseStatus.SUCCESS, "Playlist data retrieved successfully", data)
    except Exception as error:
        return create_response(ResponseStatus.ERROR, str(error), None)


def get_service_playlist(request, genre_name, service_name):
    try:
        if not transformed_playlists_collection:
            return create_response(ResponseStatus.ERROR, "Database connection not available", None)
        
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
    try:
        if not playlists_collection:
            return create_response(ResponseStatus.ERROR, "Database connection not available", None)
        
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
    try:
        if not raw_playlists_collection:
            return create_response(ResponseStatus.ERROR, "Database connection not available", None)
        
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
