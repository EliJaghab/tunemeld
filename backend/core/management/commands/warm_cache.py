import logging

from core.management.commands.playlist_etl_modules.e_clear_and_warm_track_cache import (
    Command as ClearAndWarmTrackCacheCommand,
)
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear Redis cache and warm GraphQL cache with frontend queries"

    def handle(self, *args, **options):
        logger.info("Clearing Redis cache and warming GraphQL cache...")
        cache_command = ClearAndWarmTrackCacheCommand()
        cache_command.handle(*args, **options)
        logger.info("Cache cleared and warmed successfully!")
