import json
import os

from core.models import PlaylistModel as Playlist
from core.models import RawPlaylistData, ServiceTrack
from django.core.management.base import BaseCommand

from playlist_etl.constants import ServiceName
from playlist_etl.helpers import get_logger
from playlist_etl.models import NormalizedTrack
from playlist_etl.services import AppleMusicService, SpotifyService

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Normalize raw playlist JSON data into Playlist and ServiceTrack tables"

    def handle(self, *args: object, **options: object) -> None:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        from playlist_etl.utils import WebDriverManager

        webdriver_manager = WebDriverManager()

        self.spotify_service = SpotifyService(client_id, client_secret, webdriver_manager)
        self.apple_music_service = AppleMusicService()
        Playlist.objects.all().delete()
        ServiceTrack.objects.all().delete()
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
        """Create ServiceTrack and Playlist records from raw playlist data."""

        if raw_data.service.name == ServiceName.SPOTIFY:
            tracks_data = self.parse_spotify_tracks(raw_data.data)
        elif raw_data.service.name == ServiceName.APPLE_MUSIC:
            tracks_data = self.parse_apple_music_tracks(raw_data.data)
        elif raw_data.service.name == ServiceName.SOUNDCLOUD:
            tracks_data = self.parse_soundcloud_tracks(raw_data.data)
        else:
            raise ValueError(f"Unknown service: {raw_data.service.name}")

        # Create ServiceTrack records (only for tracks with ISRC)
        service_tracks = []
        for track in tracks_data:
            if track.isrc:  # Only create ServiceTrack if ISRC is available
                service_track = ServiceTrack(
                    service=raw_data.service,
                    genre=raw_data.genre,
                    position=track.position,
                    track_name=track.name,
                    artist_name=track.artist,
                    album_name=track.album,
                    service_url=track.service_url,
                    isrc=track.isrc,
                    album_cover_url=track.album_cover_url,
                )
                service_tracks.append(service_track)

        ServiceTrack.objects.bulk_create(service_tracks)

        # Create Playlist records linked to ServiceTrack records
        created_tracks = ServiceTrack.objects.filter(service=raw_data.service, genre=raw_data.genre).order_by(
            "position"
        )

        playlists = []
        for service_track in created_tracks:
            playlist = Playlist(
                service=raw_data.service,
                genre=raw_data.genre,
                position=service_track.position,
                isrc=service_track.isrc,
                service_track=service_track,
            )
            playlists.append(playlist)

        Playlist.objects.bulk_create(playlists)
        return len(playlists)

    def parse_spotify_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse Spotify raw JSON into structured track data."""
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        return [
            NormalizedTrack(
                position=i + 1,
                name=track.get("name", ""),
                artist=", ".join(track.get("artists", [track.get("artist", "")])),
                album=track.get("album_name", ""),
                spotify_url=track.get("url", ""),
                isrc=track.get("isrc"),
                album_cover_url=track.get("cover_url"),
            )
            for i, track in enumerate(raw_data)
        ]

    def parse_apple_music_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse Apple Music raw JSON into structured track data."""
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        tracks = []
        for key, track_data in raw_data["album_details"].items():
            if key.isdigit():
                track_name = track_data["name"]
                artist_name = track_data["artist"]

                isrc = self.spotify_service.get_isrc(track_name, artist_name)

                # Only create track if ISRC was found
                if isrc:
                    apple_music_url = track_data["link"]

                    album_cover_url = self.apple_music_service.get_album_cover_url(apple_music_url)

                    track = NormalizedTrack(
                        position=int(key) + 1,
                        name=track_name,
                        artist=artist_name,
                        apple_music_url=apple_music_url,
                        album_cover_url=album_cover_url,
                        isrc=isrc,
                    )
                    tracks.append(track)

        return tracks

    def parse_soundcloud_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse SoundCloud raw JSON into structured track data."""
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        return [
            NormalizedTrack(
                position=i + 1,
                name=item["title"],
                artist=item["publisher"]["artist"],
                soundcloud_url=item["permalink"],
                isrc=item["publisher"].get("isrc"),
                album_cover_url=item.get("artwork_url"),
            )
            for i, item in enumerate(raw_data["tracks"]["items"])
            if item["publisher"].get("isrc")
        ]
