"""
Transform raw playlist data into normalized Track records.
Similar to the original MongoDB transform logic but for PostgreSQL.

Usage:
    python manage.py 03_transform
"""

from collections import defaultdict

from core.models import Playlist, RawPlaylistData, Track, TrackData, TrackPlaylist
from django.core.management.base import BaseCommand
from django.db import transaction

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Transform raw playlist data into normalized Track records and create service playlists"

    def handle(self, *args, **options):
        logger.info("Starting data transformation...")

        # Clear existing transformed data
        with transaction.atomic():
            try:
                track_count = Track.objects.count()
                track_data_count = TrackData.objects.count()
                playlist_count = Playlist.objects.count()

                TrackPlaylist.objects.all().delete()
                TrackData.objects.all().delete()
                Track.objects.all().delete()
                Playlist.objects.filter(playlist_type="service").delete()

                logger.info(f"Cleared {track_count} tracks, {track_data_count} track data, {playlist_count} playlists")
            except Exception:
                logger.info("No existing data to clear (fresh database)")

        # Get all raw playlist data
        raw_data_queryset = RawPlaylistData.objects.select_related("genre", "service").all()
        total_raw = raw_data_queryset.count()

        if total_raw == 0:
            logger.warning("No raw playlist data found. Run 02_raw_extract first.")
            return

        logger.info(f"Processing {total_raw} raw playlist records...")

        # Group tracks by (track_name, artist_name) to find duplicates across services
        track_map = defaultdict(list)

        for raw_data in raw_data_queryset:
            tracks_data = raw_data.data.get("tracks", [])
            for i, track_data in enumerate(tracks_data):
                # Extract track info
                track_name = track_data.get("name") or track_data.get("title", f"Track {i + 1}")
                artist_name = track_data.get("artist") or track_data.get("artist_name", "Unknown Artist")

                # Create track key
                track_key = (track_name.lower().strip(), artist_name.lower().strip())

                # Store track info with source context
                track_info = {
                    "raw_data": raw_data,
                    "track_data": track_data,
                    "position": i + 1,
                    "track_name": track_name,
                    "artist_name": artist_name,
                }
                track_map[track_key].append(track_info)

        # Create unique tracks
        created_tracks = {}
        tracks_created = 0

        for track_key, track_instances in track_map.items():
            # Use the first instance as the canonical track
            canonical = track_instances[0]

            track = Track.objects.create(
                track_name=canonical["track_name"],
                artist_name=canonical["artist_name"],
                # ISRC would be extracted here if available in the data
            )
            created_tracks[track_key] = track
            tracks_created += 1

        logger.info(f"Created {tracks_created} unique tracks")

        # Create track data and playlists for each service/genre combination
        playlists_created = 0
        track_data_created = 0

        for raw_data in raw_data_queryset:
            # Create playlist for this service/genre
            playlist = Playlist.objects.create(service=raw_data.service, genre=raw_data.genre, playlist_type="service")
            playlists_created += 1

            # Process tracks for this playlist
            tracks_data = raw_data.data.get("tracks", [])
            for i, track_data in enumerate(tracks_data):
                track_name = track_data.get("name") or track_data.get("title", f"Track {i + 1}")
                artist_name = track_data.get("artist") or track_data.get("artist_name", "Unknown Artist")
                track_key = (track_name.lower().strip(), artist_name.lower().strip())

                track = created_tracks[track_key]

                # Create service-specific track data
                service_track_id = track_data.get("id", f"track_{i + 1}")
                service_url = (
                    track_data.get("url")
                    or track_data.get("track_url")
                    or track_data.get("external_urls", {}).get("spotify")
                    or ""
                )

                duration_ms = track_data.get("duration_ms") or track_data.get("duration")
                popularity = (
                    track_data.get("popularity") or track_data.get("view_count") or track_data.get("play_count")
                )

                TrackData.objects.create(
                    track=track,
                    service=raw_data.service,
                    service_track_id=str(service_track_id),
                    service_url=service_url,
                    duration_ms=int(duration_ms) if duration_ms else None,
                    popularity_score=int(popularity) if popularity else None,
                )
                track_data_created += 1

                # Link track to playlist with position
                TrackPlaylist.objects.create(
                    track=track,
                    playlist=playlist,
                    position=i + 1,
                    view_count_contribution=int(popularity) if popularity else None,
                )

        logger.info(
            f"Transformation complete: {tracks_created} tracks, "
            f"{track_data_created} track data entries, {playlists_created} playlists"
        )
