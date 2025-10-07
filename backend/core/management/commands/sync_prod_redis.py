from pathlib import Path
from typing import Any

import redis
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from dotenv import dotenv_values

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Sync production Redis cache to local Redis for development"

    def handle(self, *args: Any, **options: Any) -> None:
        env_prod_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env.production"

        if not env_prod_path.exists():
            raise ValueError(f".env.production file not found at {env_prod_path}")

        prod_env = dotenv_values(env_prod_path)
        prod_redis_url = prod_env.get("REDIS_URL")

        if not prod_redis_url:
            raise ValueError("REDIS_URL not found in .env.production file")

        local_redis_url = "redis://localhost:6379/1"

        logger.info("Connecting to production Redis...")
        prod_client = redis.from_url(prod_redis_url, decode_responses=False)

        logger.info(f"Connecting to local Redis at {local_redis_url}...")
        local_client = redis.from_url(local_redis_url, decode_responses=False)

        try:
            prod_client.ping()
            logger.info("Production Redis connection successful")
        except redis.ConnectionError as e:
            raise RuntimeError(f"Failed to connect to production Redis: {e}") from e

        try:
            local_client.ping()
            logger.info("Local Redis connection successful")
        except redis.ConnectionError as e:
            raise RuntimeError(
                f"Failed to connect to local Redis: {e}. Start Redis locally with: make serve-redis"
            ) from e

        logger.info("Scanning production Redis keys with tunemeld-prod prefix...")
        pattern = "tunemeld-prod:*"
        cursor = 0
        total_keys = 0
        synced_keys = 0

        while True:
            cursor, keys = prod_client.scan(cursor, match=pattern, count=100)
            total_keys += len(keys)

            for key in keys:
                try:
                    ttl = prod_client.ttl(key)
                    value = prod_client.get(key)

                    if value is not None:
                        local_key = key.decode() if isinstance(key, bytes) else key
                        local_key = local_key.replace("tunemeld-prod:", "tunemeld-dev:")

                        if ttl > 0:
                            local_client.setex(local_key, ttl, value)
                        else:
                            local_client.set(local_key, value)

                        synced_keys += 1

                        if synced_keys % 10 == 0:
                            logger.info(f"Synced {synced_keys}/{total_keys} keys...")
                except Exception as e:
                    logger.warning(f"Failed to sync key {key}: {e}")

            if cursor == 0:
                break

        logger.info(f"Sync complete! Synced {synced_keys}/{total_keys} keys from production to local Redis")
