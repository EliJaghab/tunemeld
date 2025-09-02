from core.models import ServiceTrack, Track
from core.services.apple_music_service import get_apple_music_album_cover_url
from core.services.youtube_service import get_youtube_url
from core.utils.helpers import get_logger
from django.core.management.base import BaseCommand

from playlist_etl.constants import ServiceName

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Create canonical Track records from ServiceTrack records by ISRC"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args: object, **options: object) -> None:
        Track.objects.all().delete()

        unique_isrcs = self.get_unique_isrcs()

        if not unique_isrcs:
            return

        for isrc in unique_isrcs:
            service_tracks = ServiceTrack.objects.filter(isrc=isrc)
            self.create_canonical_track(isrc, service_tracks)

    def get_unique_isrcs(self) -> list[str]:
        """Get all unique ISRCs that have ServiceTrack records."""
        return ServiceTrack.objects.values_list("isrc", flat=True).distinct().order_by("isrc")

    def choose_primary_service_track(self, service_tracks) -> ServiceTrack | None:
        """Choose the primary ServiceTrack based on service priority."""
        # Priority: Spotify > Apple Music > SoundCloud

        for service_name in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD]:
            for track in service_tracks:
                if track.service.name == service_name:
                    return track

        # Fallback to first track if no priority service found
        return service_tracks.first() if service_tracks else None

    def create_canonical_track(self, isrc: str, service_tracks) -> Track | None:
        """Create a canonical Track record from multiple ServiceTrack records."""

        primary_track = self.choose_primary_service_track(service_tracks)
        if not primary_track:
            return None

        track_data = {
            "isrc": isrc,
            "track_name": primary_track.track_name,
            "artist_name": primary_track.artist_name,
            "album_name": primary_track.album_name,
            "album_cover_url": primary_track.album_cover_url,
        }

        apple_music_url = None
        for service_track in service_tracks:
            service_name = service_track.service.name

            if service_name == ServiceName.SPOTIFY:
                track_data["spotify_url"] = service_track.service_url
            elif service_name == ServiceName.APPLE_MUSIC:
                track_data["apple_music_url"] = service_track.service_url
                apple_music_url = service_track.service_url
            elif service_name == ServiceName.SOUNDCLOUD:
                track_data["soundcloud_url"] = service_track.service_url

        if not track_data["album_cover_url"] and apple_music_url:
            album_cover_url = get_apple_music_album_cover_url(apple_music_url)
            if album_cover_url:
                track_data["album_cover_url"] = album_cover_url

        youtube_url = get_youtube_url(primary_track.track_name, primary_track.artist_name)
        if youtube_url:
            track_data["youtube_url"] = youtube_url

        track = Track.objects.create(**track_data)
        service_tracks.update(track=track)

        return track
