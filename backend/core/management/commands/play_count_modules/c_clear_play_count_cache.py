import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear play count cache"

    def handle(self, *args, **options):
        # Play count ETL should NOT clear playlist cache as it doesn't modify playlist data
        # Only clear play count specific cache if we had any
        logger.info("Play count ETL does not need to clear playlist cache - playlist data unchanged")
