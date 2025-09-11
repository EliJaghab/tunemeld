import concurrent.futures
from datetime import UTC, datetime

from core.management.commands.view_count.b2_extract_youtube import Command as YouTubeCommand
from core.management.commands.view_count.b_extract_spotify import Command as SpotifyCommand
from core.management.commands.view_count.c_load_view_counts import Command as LoadCommand
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete view count ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit number of tracks per service")
        parser.add_argument("--service", choices=["spotify", "youtube"], help="Process only specific service")

    def handle(self, *args, **options):
        start_time = datetime.now(UTC)
        logger.info("VIEW COUNT ETL PIPELINE")
        logger.info(f"Started at: {start_time}")

        limit = options.get("limit")
        service_filter = options.get("service")

        spotify_data: dict[str, dict] = {}
        youtube_data: dict[str, dict] = {}

        if not service_filter:
            logger.info("Running Spotify and YouTube extractions in parallel...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures: dict[str, concurrent.futures.Future] = {}

                spotify_cmd = SpotifyCommand()
                youtube_cmd = YouTubeCommand()

                futures["spotify"] = executor.submit(spotify_cmd.handle, **{"limit": limit})
                futures["youtube"] = executor.submit(youtube_cmd.handle, **{"limit": limit})

                for service_name, future in futures.items():
                    try:
                        result = future.result()
                        if service_name == "spotify":
                            spotify_data = result or {}
                        else:
                            youtube_data = result or {}
                        logger.info(f"{service_name.title()} extraction completed: {len(result or {})} records")
                    except Exception as e:
                        logger.error(f"{service_name.title()} extraction failed: {e}")
        else:
            if service_filter == "spotify":
                spotify_cmd = SpotifyCommand()
                try:
                    spotify_data = spotify_cmd.handle(**{"limit": limit}) or {}
                    logger.info(f"Spotify extraction completed: {len(spotify_data)} records")
                except Exception as e:
                    logger.error(f"Spotify extraction failed: {e}")

            elif service_filter == "youtube":
                youtube_cmd = YouTubeCommand()
                try:
                    youtube_data = youtube_cmd.handle(**{"limit": limit}) or {}
                    logger.info(f"YouTube extraction completed: {len(youtube_data)} records")
                except Exception as e:
                    logger.error(f"YouTube extraction failed: {e}")

        total_extracted = len(spotify_data) + len(youtube_data)
        logger.info(f"Total extracted: {total_extracted}")

        if spotify_data or youtube_data:
            try:
                load_cmd = LoadCommand()
                load_stats = load_cmd.load_view_counts(spotify_data, youtube_data)
                logger.info(
                    f"Loading completed: {load_stats.get('total_loaded', 0)} loaded, "
                    f"{load_stats.get('total_errors', 0)} errors"
                )
            except Exception as e:
                logger.error(f"Loading stage failed: {e}")
        else:
            logger.info("No data to load")

        end_time = datetime.now(UTC)
        duration = end_time - start_time
        logger.info(f"Duration: {duration}")
