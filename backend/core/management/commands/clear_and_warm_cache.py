# PURPOSE: Manual GraphQL cache management during development/debugging
# Used when you want to clear cache and warm it fresh
# Different from automatic startup warming in apps.py

import logging

from core.utils.local_cache import CachePrefix, _execute_cache_warming_queries, local_cache_clear
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm GraphQL cache"

    def handle(self, *args, **options):
        # Clear caches
        local_cache_clear(CachePrefix.GQL_PLAYLIST_METADATA)
        local_cache_clear(CachePrefix.GQL_PLAYLIST)
        logger.info("GraphQL cache cleared")

        # Warm caches
        _execute_cache_warming_queries()
        logger.info("GraphQL cache warmed")
