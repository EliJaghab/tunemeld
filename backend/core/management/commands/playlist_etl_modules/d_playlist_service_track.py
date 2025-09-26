import json

from core.constants import ServiceName
from core.models import PlaylistModel as Playlist
from core.models import RawPlaylistData, ServiceTrack
from core.models.track import NormalizedTrack
from core.services.apple_music_service import get_apple_music_album_cover_url
from core.services.spotify_service import get_spotify_isrc
from core.utils.utils import clean_unicode_text, get_logger, process_in_parallel
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Normalize raw playlist JSON data into Playlist and ServiceTrack tables"

    def handle(self, *args: object, **options: object) -> None:
        raw_data_queryset = RawPlaylistData.objects.select_related("genre", "service").all()
        total_raw = raw_data_queryset.count()

        if total_raw == 0:
            logger.warning("No raw playlist data found. Run b_raw_extract first.")
            return

        logger.info(f"Processing {total_raw} raw playlist records...")

        total_tracks = 0

        for raw_data in raw_data_queryset:
            # Skip TuneMeld service as it's created by the aggregate step
            if raw_data.service.name == ServiceName.TUNEMELD.value:
                continue

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

        position = 1

        for track in tracks_data:
            if track.isrc:
                ServiceTrack.objects.update_or_create(
                    service=raw_data.service,
                    genre=raw_data.genre,
                    position=position,
                    defaults={
                        "track_name": track.name,
                        "artist_name": track.artist,
                        "album_name": track.album,
                        "service_url": track.service_url,
                        "isrc": track.isrc,
                        "album_cover_url": track.album_cover_url,
                    },
                )
                position += 1

        created_tracks = ServiceTrack.objects.filter(service=raw_data.service, genre=raw_data.genre).order_by(
            "position"
        )

        playlist_count = 0
        for service_track in created_tracks:
            Playlist.objects.update_or_create(
                service=raw_data.service,
                genre=raw_data.genre,
                position=service_track.position,
                defaults={
                    "isrc": service_track.isrc,
                    "service_track": service_track,
                },
            )
            playlist_count += 1

        return playlist_count

    def parse_spotify_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse Spotify raw JSON into structured track data."""
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        return [
            NormalizedTrack(
                position=i + 1,
                name=clean_unicode_text(track["name"]),
                artist=clean_unicode_text(", ".join(track["artists"]) if "artists" in track else track["artist"]),
                album=clean_unicode_text(track["album_name"]),
                spotify_url=track["url"],
                isrc=track["isrc"],
                album_cover_url=track["cover_url"],
            )
            for i, track in enumerate(raw_data)
            if track.get("isrc")
        ]

    def parse_apple_music_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse Apple Music raw JSON into structured track data."""
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        # Prepare track data for parallel processing
        track_items = [(key, track_data) for key, track_data in raw_data["album_details"].items() if key.isdigit()]

        results = process_in_parallel(
            items=track_items,
            process_func=lambda item: self.process_apple_music_track(item[0], item[1]),
            max_workers=8,
            log_progress=False,
        )

        # Collect successful results
        tracks = []
        for item, track, exc in results:
            if exc:
                _key, track_data = item
                logger.error(f"Failed to process Apple Music track {track_data['name']}: {exc}")
            elif track:
                tracks.append(track)

        tracks.sort(key=lambda x: x.position)
        return tracks

    def process_apple_music_track(self, key: str, track_data: dict) -> NormalizedTrack | None:
        """Process a single Apple Music track to get ISRC."""
        track_name = clean_unicode_text(track_data["name"])
        artist_name = clean_unicode_text(track_data["artist"])

        isrc = get_spotify_isrc(track_name, artist_name)

        # Only create track if ISRC was found
        if isrc:
            apple_music_url = track_data["link"]
            album_cover_url = get_apple_music_album_cover_url(apple_music_url)

            return NormalizedTrack(
                position=int(key) + 1,
                name=track_name,
                artist=artist_name,
                apple_music_url=apple_music_url,
                album_cover_url=album_cover_url,
                isrc=isrc,
            )
        return None

    def parse_soundcloud_tracks(self, raw_data: dict) -> list[NormalizedTrack]:
        """Parse SoundCloud raw JSON into structured track data."""
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        return [
            NormalizedTrack(
                position=i + 1,
                name=clean_unicode_text(item["title"]),
                artist=clean_unicode_text(item["publisher"]["artist"]),
                soundcloud_url=item["permalink"],
                isrc=item["publisher"]["isrc"],
                album_cover_url=item["artworkUrl"],
            )
            for i, item in enumerate(raw_data["tracks"]["items"])
            if item["publisher"].get("isrc")
        ]
