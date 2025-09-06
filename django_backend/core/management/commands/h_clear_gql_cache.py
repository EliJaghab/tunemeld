import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear GraphQL and other non-RapidAPI caches"

    def handle(self, *args, **options):
        cache.clear()
        logger.info("GraphQL and other caches cleared")
        logger.info("Note: RapidAPI cache clearing is handled separately by c_clear_raw_playlist_cache")
        logger.info("Cache clearing completed")
