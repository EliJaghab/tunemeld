"""
Phase 3: Normalize Raw Playlist Data into Structured Format

WHAT THIS DOES:
Converts messy raw JSON from different services (Spotify, Apple Music, SoundCloud)
into clean playlist positioning data. Extracts only ISRC and position information
for playlist relationships, not track metadata.

INPUT:
- RawPlaylistData records containing raw JSON blobs from each service's API
- Each service has different JSON structure and field names

OUTPUT:
- PlaylistTrack records (positioning table linking ISRC to playlist positions)
- Track records (incomplete initially - missing ISRCs for Apple Music)
- Apple Music tracks will have null ISRC until resolved in Phase D
"""

import json

from core.models import PlaylistTrack, RawPlaylistData, Track
from django.core.management.base import BaseCommand

from playlist_etl.constants import ServiceName
from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Normalize raw playlist JSON data into PlaylistTrack positioning records"

    def handle(self, *args, **options) -> None:
        PlaylistTrack.objects.all().delete()
        Track.objects.all().delete()
        raw_data_queryset = RawPlaylistData.objects.select_related("genre", "service").all()
        total_raw = raw_data_queryset.count()

        if total_raw == 0:
            logger.warning("No raw playlist data found. Run b_raw_extract first.")
            return

        logger.info(f"Processing {total_raw} raw playlist records...")

        total_tracks = 0

        for raw_data in raw_data_queryset:
            track_count = self.create_playlists(raw_data)
            total_tracks += track_count
            logger.info(f"Created {raw_data.service.name}/{raw_data.genre.name}: {track_count} positions")

        logger.info(f"Transformation complete: {total_tracks} playlist positions created")

    def create_playlists(self, raw_data: RawPlaylistData) -> int:
        """Create PlaylistTrack positioning records and Track metadata from raw playlist data."""

        if raw_data.service.name == ServiceName.SPOTIFY:
            tracks_data = self.parse_spotify_tracks(raw_data.data)
        elif raw_data.service.name == ServiceName.APPLE_MUSIC:
            tracks_data = self.parse_apple_music_tracks(raw_data.data)
        elif raw_data.service.name == ServiceName.SOUNDCLOUD:
            tracks_data = self.parse_soundcloud_tracks(raw_data.data)
        else:
            raise ValueError(f"Unknown service: {raw_data.service.name}")

        playlist_tracks = []

        for track_data in tracks_data:
            isrc = track_data.get("external_ids", {}).get("isrc")

            playlist_track = PlaylistTrack(
                service=raw_data.service,
                genre=raw_data.genre,
                position=track_data["position"],
                isrc=isrc,
            )
            playlist_tracks.append(playlist_track)

            if isrc:
                track, created = Track.objects.get_or_create(
                    isrc=isrc,
                    defaults={
                        "track_name": track_data["name"],
                        "artist_name": track_data["artist"],
                        "album_name": track_data.get("album"),
                        "spotify_url": track_data.get("external_urls", {}).get("spotify"),
                        "apple_music_url": track_data.get("external_urls", {}).get("apple_music"),
                        "soundcloud_url": track_data.get("external_urls", {}).get("soundcloud"),
                        "duration_ms": track_data.get("duration_ms"),
                        "preview_url": track_data.get("preview_url"),
                        "album_cover_url": track_data.get("album_cover_url"),
                    },
                )

                if not created:
                    self.update_track_from_service(track, track_data, raw_data.service.name)

        PlaylistTrack.objects.bulk_create(playlist_tracks)
        return len(playlist_tracks)

    def update_track_from_service(self, track: Track, track_data: dict, service_name: str) -> None:
        """Update track with service-specific URLs only."""
        updated = False

        if service_name == ServiceName.SPOTIFY:
            if not track.spotify_url and track_data.get("external_urls", {}).get("spotify"):
                track.spotify_url = track_data["external_urls"]["spotify"]
                updated = True
            if not track.album_cover_url and track_data.get("album_cover_url"):
                track.album_cover_url = track_data["album_cover_url"]
                updated = True

        elif service_name == ServiceName.APPLE_MUSIC:
            if not track.apple_music_url and track_data.get("external_urls", {}).get("apple_music"):
                track.apple_music_url = track_data["external_urls"]["apple_music"]
                updated = True

        elif service_name == ServiceName.SOUNDCLOUD:
            if not track.soundcloud_url and track_data.get("external_urls", {}).get("soundcloud"):
                track.soundcloud_url = track_data["external_urls"]["soundcloud"]
                updated = True
            if not track.album_cover_url and track_data.get("album_cover_url"):
                track.album_cover_url = track_data["album_cover_url"]
                updated = True

        if updated:
            track.save()

    def parse_spotify_tracks(self, raw_data: dict) -> list[dict]:
        """Parse Spotify raw JSON into structured track data."""
        tracks = []

        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        for i, item in enumerate(raw_data["items"]):
            track_info = item["track"]
            if not track_info:
                continue

            album_images = track_info.get("album", {}).get("images", [])
            album_cover_url = album_images[0]["url"] if album_images else None

            track = {
                "position": i + 1,
                "service_track_id": track_info.get("id"),
                "name": track_info.get("name"),
                "artist": ", ".join(artist["name"] for artist in track_info.get("artists", [])),
                "album": track_info.get("album", {}).get("name"),
                "duration_ms": track_info.get("duration_ms"),
                "popularity": track_info.get("popularity"),
                "external_ids": track_info.get("external_ids", {}),
                "external_urls": track_info.get("external_urls", {}),
                "preview_url": track_info.get("preview_url"),
                "album_cover_url": album_cover_url,
            }
            tracks.append(track)

        return tracks

    def parse_apple_music_tracks(self, raw_data: dict) -> list[dict]:
        """Parse Apple Music raw JSON into structured track data."""
        tracks = []

        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        for key, track_data in raw_data["album_details"].items():
            if key.isdigit():
                track = {
                    "position": int(key) + 1,
                    "service_track_id": track_data.get("id"),
                    "name": track_data.get("name"),
                    "artist": track_data.get("artist"),
                    "album": track_data.get("album"),
                    "duration_ms": None,
                    "popularity": None,
                    "external_ids": {},
                    "external_urls": {"apple_music": track_data.get("link")},
                    "preview_url": track_data.get("preview_url"),
                    "album_cover_url": None,
                }
                tracks.append(track)

        return tracks

    def parse_soundcloud_tracks(self, raw_data: dict) -> list[dict]:
        """Parse SoundCloud raw JSON into structured track data."""
        tracks = []

        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        for i, item in enumerate(raw_data["tracks"]["items"]):
            isrc = item["publisher"]["isrc"]
            if not isrc:
                continue

            track_name = item["title"]
            artist_name = item["user"]["name"]

            if " - " in track_name:
                artist_name, track_name = track_name.split(" - ", 1)

            track = {
                "position": i + 1,
                "service_track_id": item.get("id"),
                "name": track_name,
                "artist": artist_name,
                "album": None,
                "duration_ms": item.get("duration"),
                "popularity": item.get("play_count"),
                "external_ids": {"isrc": isrc},
                "external_urls": {"soundcloud": item.get("permalink")},
                "preview_url": item.get("stream_url"),
                "album_cover_url": item.get("artworkUrl"),
            }
            tracks.append(track)

        return tracks
