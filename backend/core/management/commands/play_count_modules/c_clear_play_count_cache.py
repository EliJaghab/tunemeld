import logging

from core.utils.local_cache import CachePrefix, local_cache_clear
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear play count cache"

    def handle(self, *args, **options):
        gql_playlist_cleared = local_cache_clear(CachePrefix.GQL_PLAYLIST)
        gql_metadata_cleared = local_cache_clear(CachePrefix.GQL_PLAYLIST_METADATA)
        total_cleared = gql_playlist_cleared + gql_metadata_cleared
        logger.info(f"Cleared {total_cleared} play count cache entries")
