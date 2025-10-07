from typing import Any

from core.management.commands.sync_prod_db import Command as DBCommand
from core.management.commands.sync_prod_redis import Command as RedisCommand
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Sync production database and Redis cache to local"

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Syncing production Redis cache...")
        redis_cmd = RedisCommand()
        redis_cmd.handle(*args, **options)

        logger.info("Syncing production database...")
        db_cmd = DBCommand()
        db_cmd.handle(*args, **options)

        logger.info("Production sync complete!")
