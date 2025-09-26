import logging
import os

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        logger.debug(f"STATIC_URL: {settings.STATIC_URL}")
        logger.debug(f"STATIC_ROOT: {settings.STATIC_ROOT}")

        if not os.getenv("GITHUB_ACTIONS"):
            try:
                # Import commands here to avoid circular imports
                from core.management.commands.play_count_modules.c_clear_and_warm_play_count_cache import (
                    Command as PlayCountCacheCommand,
                )
                from core.management.commands.playlist_etl_modules.g_clear_and_warm_track_cache import (
                    Command as TrackCacheCommand,
                )

                # Warm track/playlist cache
                track_command = TrackCacheCommand()
                track_command.handle()

                # Warm play count cache
                play_count_command = PlayCountCacheCommand()
                play_count_command.handle()
            except Exception as e:
                logger.warning(f"Failed to warm caches on startup: {e}")
        else:
            logger.info("Skipping cache warming (running in GitHub Actions)")
