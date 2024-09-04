from django.http import HttpResponse, JsonResponse

from . import (
    playlists_collection,
    raw_playlists_collection,
    track_views_collection,
    transformed_playlists_collection,
)


def root(request):
    return HttpResponse("Welcome to the Tunemeld Backend!")


def get_graph_data(request, genre_name):
    if not genre_name:
        return JsonResponse({"error": "Genre is required"}, status=400)

    try:
        count = playlists_collection.count_documents({"genre_name": genre_name})
        if count == 0:
            return JsonResponse({"message": "No data available for this genre"}, status=200)

        playlists = playlists_collection.find({"genre_name": genre_name})

        # Extract ISRCs and associated track details
        isrc_list = [
            {
                "isrc": track["isrc"],
                "track_name": track["track_name"],
                "artist_name": track["artist_name"],
                "youtube_url": track.get("youtube_url", ""),
                "album_cover_url": track.get("album_cover_url", ""),
            }
            for playlist in playlists
            for track in playlist["tracks"]
            if track.get("isrc")
        ]

        if not isrc_list:
            return JsonResponse({"error": "No ISRCs found for the specified genre"}, status=404)

        track_views_query = {"isrc": {"$in": [track["isrc"] for track in isrc_list]}}
        track_views = track_views_collection.find(track_views_query)

        response_data = []
        for track in isrc_list:
            view_data = next((view for view in track_views if view["isrc"] == track["isrc"]), None)

            spotify_views = (
                [
                    [entry["current_timestamp"], entry["delta_count"]]
                    for entry in view_data.get("view_counts", {}).get("Spotify", [])
                ]
                if view_data
                else []
            )

            youtube_views = (
                [
                    [entry["current_timestamp"], entry["delta_count"]]
                    for entry in view_data.get("view_counts", {}).get("Youtube", [])
                ]
                if view_data
                else []
            )

            response_data.append(
                {
                    "isrc": track["isrc"],
                    "track_name": track["track_name"],
                    "artist_name": track["artist_name"],
                    "youtube_url": track["youtube_url"],
                    "album_cover_url": track["album_cover_url"],
                    "view_counts": {"Spotify": spotify_views, "Youtube": youtube_views},
                }
            )

        return JsonResponse(response_data, safe=False)

    except Exception as error:
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
