from core.models import Genre, RawPlaylistData, Service
from core.services.apple_music_service import get_apple_music_playlist
from core.services.soundcloud_service import get_soundcloud_playlist
from core.services.spotify_service import get_spotify_playlist
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS, ServiceName

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract raw playlist data from RapidAPI and save to PostgreSQL"

    def handle(self, *args: object, **options: object) -> None:
        RawPlaylistData.objects.all().delete()

        supported_services = [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value, ServiceName.SPOTIFY.value]

        # Create list of all service/genre combinations to process
        tasks = []
        for service_name in SERVICE_CONFIGS:
            if service_name not in supported_services:
                continue
            for genre in PLAYLIST_GENRES:
                tasks.append((service_name, genre))

        # Process tasks in parallel using helper
        from core.utils.utils import process_in_parallel

        results = process_in_parallel(
            items=tasks,
            process_func=lambda task: self.get_and_save_playlist(task[0], task[1]),
            max_workers=2,
            log_progress=False,
        )

        for task, _result, exc in results:
            service_name, genre = task
            if exc:
                logger.error(f"Failed {service_name}/{genre}: {exc}")
                raise CommandError(f"ETL step failed on {service_name}/{genre}: {exc}") from exc
            else:
                logger.info(f"Completed {service_name}/{genre}")

    def get_and_save_playlist(self, service_name: str, genre: str) -> RawPlaylistData | None:
        logger.info(f"Getting playlist data for {service_name}/{genre}")
        service = Service.objects.get(name=service_name)
        genre_obj = Genre.objects.get(name=genre)

        try:
            # Get playlist data using appropriate function
            if service_name == ServiceName.APPLE_MUSIC:
                playlist_data = get_apple_music_playlist(genre)
            elif service_name == ServiceName.SOUNDCLOUD:
                playlist_data = get_soundcloud_playlist(genre)
            elif service_name == ServiceName.SPOTIFY:
                playlist_data = get_spotify_playlist(genre)
            else:
                raise ValueError(f"Unknown service: {service_name}")

            metadata = playlist_data["metadata"]
            tracks = playlist_data["tracks"]

            raw_data = RawPlaylistData(
                genre=genre_obj,
                service=service,
                playlist_url=metadata["playlist_url"],
                playlist_name=metadata["playlist_name"],
                playlist_cover_url=metadata.get("playlist_cover_url", ""),
                playlist_cover_description_text=metadata.get("playlist_cover_description_text", ""),
                data=tracks,
            )
            raw_data.save()
            return raw_data

        except Exception:
            raise
