import json
import os

import spotipy
from core.models import PlaylistModel as Playlist
from core.models import RawPlaylistData, ServiceTrack
from django.core.management.base import BaseCommand
from spotipy.oauth2 import SpotifyClientCredentials

from playlist_etl.constants import ServiceName
from playlist_etl.helpers import get_logger
from playlist_etl.models import NormalizedTrack
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService
from playlist_etl.utils import CacheManager

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Normalize raw playlist JSON data into Playlist and ServiceTrack tables"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.spotify_client = None
        self.apple_music_service: AppleMusicService | None = None
        self._setup_spotify_client()
        self._setup_apple_music_service()

    def _setup_spotify_client(self) -> None:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if client_id and client_secret:
            try:
                client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                self.spotify_client = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            except Exception:
                self.spotify_client = None

    def _setup_apple_music_service(self) -> None:
        try:
            mongo_client = MongoDBClient()
            cache_manager = CacheManager(mongo_client, "album_cover_cache")
            self.apple_music_service = AppleMusicService(cache_service=cache_manager)
        except Exception:
            self.apple_music_service = None

    def lookup_isrc_from_spotify(self, track_name: str, artist_name: str) -> str | None:
        if not self.spotify_client:
            return None

        try:
            query = f"track:{track_name} artist:{artist_name}"
            results = self.spotify_client.search(q=query, type="track", limit=1)

            if results["tracks"]["items"]:
                track = results["tracks"]["items"][0]
                external_ids = track.get("external_ids", {})
                if isinstance(external_ids, dict):
                    return external_ids.get("isrc")
                return None
        except Exception:
            pass

        return None

    def handle(self, *args: object, **options: object) -> None:
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
                name=item["track"]["name"],
                artist=", ".join(artist["name"] for artist in item["track"]["artists"]),
                album=item["track"]["album"]["name"],
                spotify_url=item["track"]["external_urls"]["spotify"],
                isrc=item["track"]["external_ids"].get("isrc"),
                duration=item["track"]["duration_ms"],
                preview_url=item["track"]["preview_url"],
                album_cover_url=item["track"]["album"]["images"][0]["url"]
                if item["track"]["album"]["images"]
                else None,
            )
            for i, item in enumerate(raw_data["items"])
            if item.get("track")
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

                isrc = self.lookup_isrc_from_spotify(track_name, artist_name)

                # Only create track if ISRC was found
                if isrc:
                    apple_music_url = track_data["link"]

                    album_cover_url = None
                    if self.apple_music_service:
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
                soundcloud_url=item["url"],
                isrc=item["publisher"].get("isrc"),
                album_cover_url=item.get("artwork_url"),
            )
            for i, item in enumerate(raw_data["tracks"]["items"])
            if item["publisher"].get("isrc")
        ]
