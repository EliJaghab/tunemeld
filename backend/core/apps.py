import logging
import os

from core.utils.local_cache import warm_local_cache_from_postgres
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        logger.debug(f"STATIC_URL: {settings.STATIC_URL}")
        logger.debug(f"STATIC_ROOT: {settings.STATIC_ROOT}")

        # Only warm cache when running on Railway production server
        if os.getenv("RAILWAY_ENVIRONMENT"):
            logger.info("Starting cache warming on Railway server startup...")
            warm_local_cache_from_postgres()
            logger.info("Cache warming completed")
        else:
            logger.info("Skipping cache warming (not on Railway)")
