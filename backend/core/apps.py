import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        logger.debug(f"STATIC_URL: {settings.STATIC_URL}")
        logger.debug(f"STATIC_ROOT: {settings.STATIC_ROOT}")

        # Import here to avoid circular imports during Django startup
        from core.utils.local_cache import warm_local_cache_from_postgres

        logger.info("Starting cache warming on server startup...")
        warm_local_cache_from_postgres()
        logger.info("Cache warming completed")
