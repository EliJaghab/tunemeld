import uuid

from core.models import Genre, RawPlaylistData, Service
from core.services.apple_music_service import get_apple_music_playlist
from core.services.soundcloud_service import get_soundcloud_playlist
from core.services.spotify_service import get_spotify_playlist
from core.utils.constants import PLAYLIST_GENRES, SERVICE_CONFIGS, GenreName, ServiceName
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract raw playlist data from RapidAPI and save to PostgreSQL"

    def handle(self, *args: object, etl_run_id: uuid.UUID, **options: object) -> None:
        supported_services = [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value, ServiceName.SPOTIFY.value]

        tasks = []
        for service_name in SERVICE_CONFIGS:
            if service_name not in supported_services:
                continue
            for genre_str in PLAYLIST_GENRES:
                genre = GenreName(genre_str)
                service = ServiceName(service_name)
                tasks.append((service, genre))

        from core.utils.utils import process_in_parallel

        results = process_in_parallel(
            items=tasks,
            process_func=lambda task: self.get_and_save_playlist(task[0], task[1], etl_run_id),
            max_workers=2,
            log_progress=False,
        )

        for task, _result, exc in results:
            task_service: ServiceName
            task_genre: GenreName
            task_service, task_genre = task
            if exc:
                logger.error(f"Failed {task_service.value}/{task_genre.value}: {exc}")
                raise CommandError(f"ETL step failed on {task_service.value}/{task_genre.value}: {exc}") from exc
            else:
                logger.info(f"Completed {task_service.value}/{task_genre.value}")

    def get_and_save_playlist(
        self, service_name: ServiceName, genre: GenreName, etl_run_id: uuid.UUID
    ) -> RawPlaylistData | None:
        logger.info(f"Getting playlist data for {service_name.value}/{genre.value}")
        service = Service.objects.get(name=service_name.value)
        genre_obj = Genre.objects.get(name=genre.value)

        try:
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

            raw_data, _created = RawPlaylistData.objects.update_or_create(
                service=service,
                genre=genre_obj,
                etl_run_id=etl_run_id,
                defaults={
                    "playlist_url": metadata["playlist_url"],
                    "playlist_name": metadata["playlist_name"],
                    "playlist_cover_url": metadata["playlist_cover_url"],
                    "playlist_cover_description_text": metadata["playlist_cover_description_text"],
                    "data": tracks,
                },
            )
            return raw_data

        except Exception:
            raise
