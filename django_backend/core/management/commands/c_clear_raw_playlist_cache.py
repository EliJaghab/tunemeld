import logging

from django.core.management.base import BaseCommand

from playlist_etl.cache_utils import CachePrefix
from playlist_etl.constants import SERVICE_CONFIGS, ServiceName
from playlist_etl.schedule_config import ScheduleConfig, is_within_scheduled_time_window

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear RapidAPI cache only if within scheduled ETL window to ensure fresh playlist data"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force clear RapidAPI cache regardless of schedule")

    def handle(self, *args, **options):
        from django.core.cache import cache

        schedule_config = ScheduleConfig()

        if options.get("force") or is_within_scheduled_time_window(schedule_config):
            if options.get("force"):
                logger.info("Force clearing RapidAPI cache (--force flag used)")
            else:
                logger.info("Within scheduled ETL window - clearing RapidAPI cache for fresh playlist data")

            cache_keys_to_clear = []
            for service_name in [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value]:
                service_config = SERVICE_CONFIGS[service_name]
                for genre in service_config["links"]:
                    if service_name == ServiceName.APPLE_MUSIC.value:
                        playlist_id = service_config["links"][genre].split("/")[-1]
                        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
                        url = f"{service_config['base_url']}?url={apple_playlist_url}"
                    else:
                        playlist_url = service_config["links"][genre]
                        url = f"{service_config['base_url']}?playlist={playlist_url}"

                    key_data = f"{service_name}:{genre}:{url}"
                    cache_keys_to_clear.append(key_data)

            from playlist_etl.cache_utils import _generate_cache_key

            cleared_count = 0
            for key_data in cache_keys_to_clear:
                cache_key = _generate_cache_key(CachePrefix.RAPIDAPI, key_data)
                if cache.get(cache_key):
                    cache.delete(cache_key)
                    cleared_count += 1
                    logger.info(f"Cleared RapidAPI cache: {key_data}")

            logger.info(f"RapidAPI cache clearing completed - {cleared_count} keys cleared")
        else:
            logger.info("Outside scheduled ETL window - preserving RapidAPI cache to avoid rate limits")
            logger.info(
                f"Next scheduled ETL: Saturdays at 5 PM UTC (±{schedule_config.cache_clear_window_minutes} min window)"
            )

        logger.info("Raw playlist cache clearing completed")
