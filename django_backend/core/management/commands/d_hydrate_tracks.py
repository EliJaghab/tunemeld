"""
Phase 4: Hydrate Tracks with ISRC Resolution and Create Canonical Records

WHAT THIS DOES:
Takes the clean structured track data from Phase 3 and resolves ISRCs to create
canonical Track objects. This is where track deduplication happens - tracks with
the same ISRC across different services are merged into one canonical Track.

INPUT:
- PlaylistTrack records from Phase 3 (normalized playlist track table)
- ISRC data stored directly in PlaylistTrack.isrc field

OUTPUT:
- Canonical Track records (one per unique ISRC)
- TrackData records (service-specific metadata linked to canonical tracks)

ISRC RESOLUTION:
- Spotify: Directly from external_ids.isrc field
- SoundCloud: Directly from publisher.isrc field
- Apple Music: Requires Spotify API lookup (track_name + artist_name → ISRC)

DEDUPLICATION LOGIC:
If "Flowers" by "Miley Cyrus" appears on both Spotify and SoundCloud with
ISRC "USSM12301546", this creates:
- 1 canonical Track with ISRC "USSM12301546"
- 2 TrackData records (one for Spotify metadata, one for SoundCloud metadata)

GRACEFUL HANDLING:
- Tracks without ISRCs are logged and skipped
- Apple Music tracks without Spotify matches are skipped (for now)
"""

import os

from core.models import PlaylistTrack, Track, TrackData
from django.core.management.base import BaseCommand
from django.db import transaction

from playlist_etl.config import ISRC_CACHE_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import SpotifyService
from playlist_etl.utils import CacheManager, WebDriverManager

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Hydrate tracks with ISRC resolution and create canonical Track records"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mongo_client = MongoDBClient()
        self.spotify_service = SpotifyService(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            isrc_cache_manager=CacheManager(mongo_client, ISRC_CACHE_COLLECTION),
            webdriver_manager=WebDriverManager(),
        )

    def handle(self, *args, **options) -> None:
        logger.info("Starting track hydration with ISRC resolution...")

        self.clear_track_data()

        playlist_tracks = PlaylistTrack.objects.select_related("service", "genre").all()
        if not playlist_tracks.exists():
            logger.warning("No playlist tracks found. Run 03_normalize_raw_playlists first.")
            return

        logger.info(f"Processing {playlist_tracks.count()} playlist tracks...")

        isrc_tracks = {}
        tracks_created = 0
        track_data_created = 0

        for playlist_track in playlist_tracks:
            isrc = self.resolve_isrc_from_playlist_track(playlist_track)

            if not isrc:
                logger.warning(
                    f"No ISRC found for {playlist_track.track_name} by {playlist_track.artist_name} "
                    f"from {playlist_track.service.name}"
                )
                continue

            if isrc not in isrc_tracks:
                track = Track.objects.create(
                    track_name=playlist_track.track_name,
                    artist_name=playlist_track.artist_name,
                    isrc=isrc,
                )
                isrc_tracks[isrc] = track
                tracks_created += 1
            else:
                track = isrc_tracks[isrc]

            service_url = self.get_service_url(playlist_track)

            TrackData.objects.create(
                track=track,
                service=playlist_track.service,
                service_track_id=str(playlist_track.service_track_id or ""),
                service_url=service_url,
                preview_url=playlist_track.preview_url or "",
            )
            track_data_created += 1

        logger.info(f"Hydration complete: {tracks_created} unique tracks, " f"{track_data_created} track data entries")

    def clear_track_data(self) -> None:
        """Clear existing track hydration data for clean rebuild."""
        with transaction.atomic():
            TrackData.objects.all().delete()
            Track.objects.all().delete()
            logger.info("Cleared existing track hydration data")

    def resolve_isrc_from_playlist_track(self, playlist_track: PlaylistTrack) -> str | None:
        """Resolve ISRC for a PlaylistTrack."""
        if playlist_track.isrc:
            return playlist_track.isrc

        if playlist_track.service.name == "AppleMusic":
            return self.spotify_service.get_isrc(playlist_track.track_name, playlist_track.artist_name)

        return None

    def get_service_url(self, playlist_track: PlaylistTrack) -> str:
        """Get the appropriate service URL for a PlaylistTrack."""
        if playlist_track.spotify_url:
            return playlist_track.spotify_url
        elif playlist_track.apple_music_url:
            return playlist_track.apple_music_url
        elif playlist_track.soundcloud_url:
            return playlist_track.soundcloud_url
        return ""
