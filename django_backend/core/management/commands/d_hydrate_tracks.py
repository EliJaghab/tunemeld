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

import re

from core.models import PlaylistTrack, Track, TrackData
from django.core.management.base import BaseCommand
from django.db import transaction

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Hydrate tracks with ISRC resolution and create canonical Track records"

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
        try:
            with transaction.atomic():
                TrackData.objects.all().delete()
                Track.objects.all().delete()
                logger.info("Cleared existing track hydration data")
        except Exception:
            logger.info("No existing track data to clear")

    def resolve_isrc_from_playlist_track(self, playlist_track: PlaylistTrack) -> str | None:
        """Resolve ISRC for a PlaylistTrack."""
        if playlist_track.isrc:
            return playlist_track.isrc

        if playlist_track.service.name == "AppleMusic":
            return self.lookup_isrc_via_spotify(playlist_track.track_name, playlist_track.artist_name)

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

    def lookup_isrc_via_spotify(self, track_name: str, artist_name: str) -> str | None:
        """
        Look up ISRC for Apple Music tracks using Spotify API.
        Mirrors the exact logic from MongoDB Transform class.
        """
        # TODO: Implement cache manager for production
        # isrc = self.isrc_cache_manager.get(cache_key)
        # if isrc:
        #     logger.info(f"Cache hit for ISRC: {cache_key}")
        #     return isrc

        logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

        track_name_no_parens = self._get_track_name_with_no_parens(track_name)
        queries = [
            f"track:{track_name_no_parens} artist:{artist_name}",
            f"{track_name_no_parens} {artist_name}",
            f"track:{track_name.lower()} artist:{artist_name}",
        ]

        for query in queries:
            isrc = self._get_isrc(query)
            if isrc:
                logger.info(f"Found ISRC for {track_name} by {artist_name}: {isrc}")
                # TODO: Cache result in production
                # self.isrc_cache_manager.set(cache_key, isrc)
                return isrc

        logger.info(f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}")
        return None

    def _get_track_name_with_no_parens(self, track_name: str) -> str:
        """Remove parentheses from track name for better search matching."""
        return re.sub(r"\([^()]*\)", "", track_name.lower())

    def _get_isrc(self, query: str) -> str | None:
        """
        Search Spotify API for track and return ISRC.
        This is a placeholder - in production, this would use actual Spotify client.
        """
        try:
            # TODO: Implement actual Spotify API search
            # results = self.spotify_client.search(q=query, type="track", limit=1)
            # tracks = results["tracks"]["items"]
            # if tracks:
            #     return tracks[0]["external_ids"].get("isrc")
            # return None
            logger.debug(f"Spotify search query: {query}")
            return None  # Placeholder - no external API calls during transformation
        except Exception as e:
            logger.info(f"Error searching Spotify with query '{query}': {e}")
            return None
