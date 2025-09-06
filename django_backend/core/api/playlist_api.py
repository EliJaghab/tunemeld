"""
PostgreSQL-based playlist API views for staging environment. WIP
"""

import logging

from core.api.utils import error_response, success_response
from core.models.d_raw_playlist import RawPlaylistData
from core.models.e_playlist import Playlist

from playlist_etl.constants import SERVICE_CONFIGS, ServiceName

logger = logging.getLogger(__name__)


def _get_service_display_name(service_name):
    """Get service display name from constants"""
    config = SERVICE_CONFIGS.get(service_name, {})
    return config.get("display_name", service_name)


def _get_service_icon_url(service_name):
    """Get service icon URL from constants"""
    config = SERVICE_CONFIGS.get(service_name, {})
    return config.get("icon_url", "")


def get_aggregate_playlist(request, genre_name):
    """Get aggregated playlist data from PostgreSQL tables."""
    try:
        playlist_positions = (
            Playlist.objects.filter(genre__name=genre_name, service__name=ServiceName.TUNEMELD)
            .select_related("service_track", "genre", "service")
            .order_by("position")
        )

        if not playlist_positions.exists():
            return error_response("No data found for the specified genre", 404)

        tracks = []
        for position in playlist_positions:
            service_track = position.service_track
            # Generate realistic fake view counts for staging TODO upgraaupgradede in next update
            import random

            youtube_views = random.randint(50000, 5000000)
            spotify_streams = random.randint(100000, 10000000)

            from core.models.e_playlist import ServiceTrack

            cross_service_tracks = ServiceTrack.objects.filter(isrc=position.isrc, genre=position.genre).select_related(
                "service"
            )

            # Build source data in the format frontend expects
            spotify_source = None
            apple_music_source = None
            soundcloud_source = None
            youtube_source = None

            primary_service_name = None
            primary_track_url = None

            for cs_track in cross_service_tracks:
                service_name = cs_track.service.name
                source_data = {
                    "url": cs_track.service_url,
                    "displayName": _get_service_display_name(service_name),
                    "iconUrl": _get_service_icon_url(service_name),
                }

                # Map to frontend expected properties
                if service_name == ServiceName.SPOTIFY:
                    spotify_source = source_data
                elif service_name == ServiceName.APPLE_MUSIC:
                    apple_music_source = source_data
                elif service_name == ServiceName.SOUNDCLOUD:
                    soundcloud_source = source_data
                elif service_name == ServiceName.YOUTUBE:
                    youtube_source = source_data

                # Use the reference service track as primary
                if cs_track.id == service_track.id:
                    primary_service_name = service_name
                    primary_track_url = cs_track.service_url

            track_data = {
                "isrc": position.isrc or "",
                "artist_name": service_track.artist_name,
                "track_name": service_track.track_name,
                "rank": position.position,
                "service": ServiceName.TUNEMELD,  # This is an aggregate playlist
                "album_cover_url": service_track.album_cover_url or "",
                "service_url": service_track.service_url,
                "source_name": primary_service_name or "Unknown",
                "track_url": primary_track_url or service_track.service_url,
                "spotifySource": spotify_source,
                "appleMusicSource": apple_music_source,
                "soundcloudSource": soundcloud_source,
                "youtubeSource": youtube_source,
                "view_count_data_json": {
                    "Youtube": {
                        "current_count_json": {"current_view_count": youtube_views},
                        "initial_count_json": {
                            "initial_view_count": int(youtube_views * 0.8)  # 80% of current for initial
                        },
                    },
                    "Spotify": {
                        "current_count_json": {"current_view_count": spotify_streams},
                        "initial_count_json": {
                            "initial_view_count": int(spotify_streams * 0.8)  # 80% of current for initial
                        },
                    },
                },
            }
            tracks.append(track_data)

        data = [{"genre_name": genre_name, "tracks": tracks}]

        return success_response(data, "tunemeld playlist data retrieved successfully")

    except Exception as error:
        logger.exception("Error in PostgreSQL get_aggregate_playlist view")
        return error_response(str(error))


def get_playlist(request, genre_name, service_name):
    """Get service-specific playlist data from PostgreSQL tables."""
    try:
        playlist_positions = (
            Playlist.objects.filter(genre__name=genre_name, service__name=service_name)
            .select_related("service_track", "genre", "service")
            .order_by("position")
        )

        if not playlist_positions.exists():
            return error_response("No data found for the specified genre and service", 404)

        tracks = []
        for position in playlist_positions:
            service_track = position.service_track
            import random

            youtube_views = random.randint(50000, 5000000)
            spotify_streams = random.randint(100000, 10000000)

            track_data = {
                "isrc": position.isrc or "",
                "artist_name": service_track.artist_name,
                "track_name": service_track.track_name,
                "rank": position.position,
                "album_cover_url": service_track.album_cover_url or "",
                "service_url": service_track.service_url,
                "source_name": position.service.name,
                "track_url": service_track.service_url,
                "additional_sources": {},  # Empty for staging
                "view_count_data_json": {
                    "Youtube": {
                        "current_count_json": {"current_view_count": youtube_views},
                        "initial_count_json": {
                            "initial_view_count": int(youtube_views * 0.8)  # 80% of current for initial
                        },
                    },
                    "Spotify": {
                        "current_count_json": {"current_view_count": spotify_streams},
                        "initial_count_json": {
                            "initial_view_count": int(spotify_streams * 0.8)  # 80% of current for initial
                        },
                    },
                },
            }
            tracks.append(track_data)

        data = [{"genre_name": genre_name, "service_name": service_name, "tracks": tracks}]

        return success_response(data, "Service playlist data retrieved successfully")

    except Exception as error:
        logger.exception("Error in PostgreSQL get_playlist view")
        return error_response(str(error))


def get_playlist_metadata(request, genre_name):
    """Get playlist metadata (cover, name, description) from PostgreSQL tables."""
    try:
        raw_playlists = RawPlaylistData.objects.filter(genre__name=genre_name)

        if not raw_playlists.exists():
            return error_response("No data found for the specified genre", 404)

        result = {}
        for playlist in raw_playlists:
            service_name = playlist.service.name
            result[service_name] = {
                "playlist_cover_url": playlist.playlist_cover_url or "",
                "playlist_cover_description_text": playlist.playlist_cover_description_text or "",
                "playlist_name": playlist.playlist_name or "",
                "playlist_url": playlist.playlist_url or "",
            }

        return success_response(result, "Playlist metadata retrieved successfully")

    except Exception as error:
        logger.exception("Error in PostgreSQL get_playlist_metadata view")
        return error_response(str(error))


def get_last_updated(request, genre_name):
    """Get last updated timestamp from PostgreSQL tables."""
    try:
        # Import here to avoid circular imports
        from core.models.e_playlist import ServiceTrack

        # Get the most recent service track update for this genre
        latest_track = ServiceTrack.objects.filter(genre__name=genre_name).order_by("-updated_at").first()

        if not latest_track:
            return error_response("No data found for the specified genre", 404)

        return success_response(
            {"last_updated": latest_track.updated_at.isoformat()}, "Last updated timestamp retrieved successfully"
        )

    except Exception as error:
        logger.exception("Error in PostgreSQL get_last_updated view")
        return error_response(str(error))
