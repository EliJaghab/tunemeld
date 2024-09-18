import logging
from typing import Dict, List

from django.http import HttpResponse, JsonResponse

from . import (
    playlists_collection,
    raw_playlists_collection,
    historical_track_views,
    transformed_playlists_collection,
)

logger = logging.getLogger(__name__)


def root(request):
    return HttpResponse("Welcome to the Tunemeld Backend!")


def health_check(request):
    return HttpResponse("OK")


def get_graph_data(request, genre_name):
    """Returns track views for all the tracks in a given aggregated playlist."""
    if not genre_name:
        return JsonResponse({"error": "Genre is required"}, status=400)

    try:

        def get_tracks_from_playlist(genre_name: str) -> Dict:
            playlists = playlists_collection.find({"genre_name": genre_name}, {'_id': False})
            tracks = [
                {
                    "isrc": track["isrc"],
                    "track_name": track["track_name"],
                    "artist_name": track["artist_name"],
                    "youtube_url": track.get("youtube_url", ""),
                    "album_cover_url": track.get("album_cover_url", ""),
                }
                for track in playlists[0]["tracks"]
            ]
            return tracks

        def get_view_counts(isrc: List[str]) -> Dict:
            """Get all the view counts in one query."""
            track_views_query = {"isrc": {"$in": isrc}}
            track_views = historical_track_views.find(track_views_query, {'_id': False})

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

        return JsonResponse(track_views, safe=False)

    except Exception as error:
        logger.exception("Error in get_graph_data view")
        return JsonResponse({"error": str(error)}, status=500)


def get_playlist_data(request, genre_name):
    if not genre_name:
        return JsonResponse({"error": "Genre is required"}, status=400)

    try:
        data = list(playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return JsonResponse({"error": "No data found for the specified genre"}, status=404)
        return JsonResponse(data, safe=False)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)


def get_service_playlist(request, genre_name, service_name):
    if not genre_name or not service_name:
        return JsonResponse({"error": "Genre and service are required"}, status=400)

    try:
        data = list(
            transformed_playlists_collection.find(
                {"genre_name": genre_name, "service_name": service_name}, {"_id": False}
            )
        )
        if not data:
            return JsonResponse(
                {"error": "No data found for the specified genre and service"}, status=404
            )
        return JsonResponse(data, safe=False)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)


def get_last_updated(request, genre_name):
    if not genre_name:
        return JsonResponse({"error": "Genre is required"}, status=400)

    try:
        data = list(playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return JsonResponse({"error": "No data found for the specified genre"}, status=404)

        last_updated = data[0]["insert_timestamp"]
        return JsonResponse({"last_updated": last_updated})
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)


def get_header_art(request, genre_name):
    if not genre_name:
        return JsonResponse({"error": "Genre is required"}, status=400)

    try:
        data = list(raw_playlists_collection.find({"genre_name": genre_name}, {"_id": False}))
        if not data:
            return JsonResponse({"error": "No data found for the specified genre"}, status=404)

        formatted_data = format_playlist_data(data)
        return JsonResponse(formatted_data, safe=False)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)


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
