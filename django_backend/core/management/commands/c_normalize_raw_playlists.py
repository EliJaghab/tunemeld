import json

from core.models import PlaylistTrack, RawPlaylistData, Track
from django.core.management.base import BaseCommand

from playlist_etl.constants import ServiceName
from playlist_etl.helpers import get_logger
from playlist_etl.models import AppleMusicTrack, NormalizedTrack, SoundCloudTrack, SpotifyTrack

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Normalize raw playlist JSON data into PlaylistTrack and Track tables"

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
            playlist_track = PlaylistTrack(
                service=raw_data.service,
                genre=raw_data.genre,
                position=track_data.position,
                isrc=track_data.isrc,
            )
            playlist_tracks.append(playlist_track)

            if track_data.isrc:
                track, created = Track.objects.get_or_create(
                    isrc=track_data.isrc,
                    defaults={
                        "track_name": track_data.name,
                        "artist_name": track_data.artist,
                        "album_name": track_data.album,
                        "spotify_url": track_data.spotify_url,
                        "apple_music_url": track_data.apple_music_url,
                        "soundcloud_url": track_data.soundcloud_url,
                        "album_cover_url": track_data.album_cover_url,
                    },
                )

                if not created:
                    self.update_track_from_service(track, track_data, raw_data.service.name)

        PlaylistTrack.objects.bulk_create(playlist_tracks)
        return len(playlist_tracks)

    def update_track_from_service(self, track: Track, track_data: NormalizedTrack, service_name: str) -> None:
        """Update track with service-specific URLs only."""
        updated = False

        if service_name == ServiceName.SPOTIFY:
            if not track.spotify_url and track_data.spotify_url:
                track.spotify_url = track_data.spotify_url
                updated = True
            if not track.album_cover_url and track_data.album_cover_url:
                track.album_cover_url = track_data.album_cover_url
                updated = True

        elif service_name == ServiceName.APPLE_MUSIC:
            if not track.apple_music_url and track_data.apple_music_url:
                track.apple_music_url = track_data.apple_music_url
                updated = True

        elif service_name == ServiceName.SOUNDCLOUD:
            if not track.soundcloud_url and track_data.soundcloud_url:
                track.soundcloud_url = track_data.soundcloud_url
                updated = True
            if not track.album_cover_url and track_data.album_cover_url:
                track.album_cover_url = track_data.album_cover_url
                updated = True

        if updated:
            track.save()

    def parse_spotify_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse Spotify raw JSON into structured track data."""
        tracks = []

        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        for i, item in enumerate(raw_data["items"]):
            track_info = item["track"]
            if not track_info:
                continue

            track = SpotifyTrack.from_raw(track_info, i + 1)
            tracks.append(track)

        return tracks

    def parse_apple_music_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse Apple Music raw JSON into structured track data."""
        tracks = []

        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        for key, track_data in raw_data["album_details"].items():
            if key.isdigit():
                track = AppleMusicTrack.from_raw(track_data, int(key) + 1)
                tracks.append(track)

        return tracks

    def parse_soundcloud_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse SoundCloud raw JSON into structured track data."""
        tracks = []

        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        for i, item in enumerate(raw_data["tracks"]["items"]):
            isrc = item["publisher"]["isrc"]
            if not isrc:
                continue

            track = SoundCloudTrack.from_raw(item, i + 1)
            tracks.append(track)

        return tracks
