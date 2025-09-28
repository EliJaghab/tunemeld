from collections import Counter

from core.constants import ServiceName
from core.models import ServiceTrack, Track
from core.services.apple_music_service import get_apple_music_album_cover_url
from core.services.soundcloud_service import get_soundcloud_url
from core.services.youtube_service import YouTubeUrlResult, get_youtube_url
from core.utils.utils import get_logger, process_in_parallel
from django.core.management.base import BaseCommand, CommandError

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Create canonical Track records from ServiceTrack records by ISRC"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args: object, **options: object) -> None:
        unique_isrcs = list(self.get_unique_isrcs())

        if not unique_isrcs:
            return

        results = process_in_parallel(
            items=unique_isrcs,
            process_func=lambda isrc: self.process_isrc(isrc),
            log_progress=True,
            progress_interval=50,
        )

        youtube_stats: Counter[YouTubeUrlResult] = Counter()
        for isrc, result, exc in results:
            if exc:
                logger.error(f"Failed to process ISRC {isrc}: {exc}")
                raise CommandError(f"Pipeline failed on ISRC {isrc}: {exc}") from exc

            if result and isinstance(result, YouTubeUrlResult):
                youtube_stats[result] += 1

        self.log_youtube_summary(len(unique_isrcs), youtube_stats)

    def log_youtube_summary(self, total_tracks: int, stats: Counter) -> None:
        """Log YouTube URL retrieval summary statistics."""
        logger.info("YouTube URL Retrieval Summary:")
        logger.info(f"- Total tracks processed: {total_tracks}")

        for result_type, count in stats.items():
            percentage = (count / total_tracks * 100) if total_tracks > 0 else 0
            logger.info(f"- {result_type.value.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    def process_isrc(self, isrc: str) -> YouTubeUrlResult | None:
        """Process a single ISRC and create canonical track."""
        service_tracks = ServiceTrack.objects.filter(isrc=isrc)
        return self.create_canonical_track(isrc, service_tracks)

    def get_unique_isrcs(self) -> list[str]:
        """Get all unique ISRCs that have ServiceTrack records."""
        return ServiceTrack.objects.all().values_list("isrc", flat=True).distinct().order_by("isrc")

    def choose_primary_service_track(self, service_tracks) -> ServiceTrack | None:
        """Choose the primary ServiceTrack based on service priority."""
        # Priority: Spotify > Apple Music > SoundCloud

        for service_name in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD]:
            for track in service_tracks:
                if track.service.name == service_name:
                    return track

        # Fallback to first track if no priority service found
        return service_tracks.first() if service_tracks else None

    def create_canonical_track(self, isrc: str, service_tracks) -> YouTubeUrlResult | None:
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
            "spotify_url": None,
            "apple_music_url": None,
            "soundcloud_url": None,
            "youtube_url": None,
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

        youtube_url, youtube_result = get_youtube_url(primary_track.track_name, primary_track.artist_name)
        if youtube_url and youtube_url != "https://youtube.com":
            track_data["youtube_url"] = youtube_url

        if not track_data["soundcloud_url"]:
            soundcloud_url, _soundcloud_result = get_soundcloud_url(primary_track.track_name, primary_track.artist_name)
            if soundcloud_url:
                track_data["soundcloud_url"] = soundcloud_url

        track, _created = Track.objects.update_or_create(isrc=isrc, defaults=track_data)
        service_tracks.update(track=track)

        return youtube_result
