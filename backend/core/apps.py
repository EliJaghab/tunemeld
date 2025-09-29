import logging
import os
import sys

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        logger.debug(f"STATIC_URL: {settings.STATIC_URL}")
        logger.debug(f"STATIC_ROOT: {settings.STATIC_ROOT}")

        # Only run cache warming for web server startup (runserver) or Railway deployment
        is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
        is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT"))

        if not os.getenv("GITHUB_ACTIONS") and (is_runserver or is_railway):
            try:
                # Circular import: commands import models, so must import inside ready()
                from core.management.commands.play_count_modules.c_clear_and_warm_play_count_cache import (
                    Command as PlayCountCacheCommand,
                )
                from core.management.commands.playlist_etl_modules.g_clear_and_warm_track_cache import (
                    Command as TrackCacheCommand,
                )

                track_command = TrackCacheCommand()
                track_command.handle()

                play_count_command = PlayCountCacheCommand()
                play_count_command.handle()
            except Exception as e:
                logger.warning(f"Failed to warm caches on startup: {e}")
        else:
            if os.getenv("GITHUB_ACTIONS"):
                logger.info("Skipping cache warming (running in GitHub Actions)")
            elif not is_runserver and not is_railway:
                command = sys.argv[1] if len(sys.argv) > 1 else "unknown"
                logger.info(f"Skipping cache warming (not runserver/Railway: {command})")
