import concurrent.futures

from core.models import Genre, RawPlaylistData, Service
from django.core.management.base import BaseCommand

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS, ServiceName
from playlist_etl.extract import (
    get_apple_music_playlist,
    get_soundcloud_playlist,
    get_spotify_playlist,
)
from playlist_etl.helpers import get_logger

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

        # Process tasks in parallel with thread pool
        max_workers = min(len(tasks), 8)  # Limit concurrent API calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.get_and_save_playlist, service_name, genre): (service_name, genre)
                for service_name, genre in tasks
            }

            for future in concurrent.futures.as_completed(future_to_task):
                service_name, genre = future_to_task[future]
                try:
                    future.result()
                    logger.info(f"Completed {service_name}/{genre}")
                except Exception as exc:
                    logger.error(f"Failed {service_name}/{genre}: {exc}")

    def get_and_save_playlist(self, service_name: str, genre: str) -> RawPlaylistData | None:
        import requests

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

        except requests.exceptions.HTTPError as e:
            if "429" in str(e) and service_name == ServiceName.APPLE_MUSIC:
                logger.warning(f"Apple Music API rate limited for {genre}. Skipping this service/genre.")
                return None
            else:
                raise
        except Exception as e:
            if "429" in str(e) and service_name == ServiceName.APPLE_MUSIC:
                logger.warning(f"Apple Music API rate limited for {genre}. Skipping this service/genre.")
                return None
            else:
                raise
