import json
from pathlib import Path

from core.utils.utils import get_logger
from django.core.management.base import BaseCommand

from playlist_etl.cache_utils import cache_set
from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS, CachePrefix, ServiceName

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Populate cache with existing real_api_data files"

    def handle(self, *args, **options):
        real_api_data_dir = Path(__file__).parent.parent.parent.parent / "real_api_data"

        if not real_api_data_dir.exists():
            logger.error(f"real_api_data directory not found: {real_api_data_dir}")
            return

        service_mapping = {
            "apple_music": ServiceName.APPLE_MUSIC.value,
            "soundcloud": ServiceName.SOUNDCLOUD.value,
            "spotify": ServiceName.SPOTIFY.value,
        }

        total_cached = 0

        for service_dir, service_name in service_mapping.items():
            service_path = real_api_data_dir / service_dir
            if not service_path.exists():
                logger.warning(f"Service directory not found: {service_path}")
                continue

            for genre in PLAYLIST_GENRES:
                json_file = service_path / f"{genre}.json"
                if not json_file.exists():
                    logger.warning(f"Data file not found: {json_file}")
                    continue

                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    # Create cache URL that matches rapid_api_client pattern
                    config = SERVICE_CONFIGS[service_name]
                    if service_name == ServiceName.APPLE_MUSIC.value:
                        playlist_id = config["links"][genre].split("/")[-1]
                        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
                        cache_url = f"{config['base_url']}?url={apple_playlist_url}"
                    elif service_name == ServiceName.SOUNDCLOUD.value:
                        playlist_url = config["links"][genre]
                        cache_url = f"{config['base_url']}?playlist={playlist_url}"
                    else:  # Spotify uses different method, skip for now
                        logger.info("Skipping Spotify caching (uses SpotDL)")
                        continue

                    # Cache the data
                    key_data = f"{service_name}:{genre}:{cache_url}"
                    cache_set(CachePrefix.RAPIDAPI, key_data, data)
                    total_cached += 1
                    logger.info(f"Cached {service_name}/{genre}")

                except Exception as e:
                    logger.error(f"Error caching {service_name}/{genre}: {e}")

        logger.info(f"Successfully cached {total_cached} API responses")
