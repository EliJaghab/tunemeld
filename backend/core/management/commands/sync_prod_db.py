import os
from pathlib import Path
from typing import Any

from core.utils.utils import get_logger
from django.core import management
from django.core.management.base import BaseCommand
from dotenv import dotenv_values

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Sync production database to local using Django ORM"

    def handle(self, *args: Any, **options: Any) -> None:
        env_prod_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env.production"

        if not env_prod_path.exists():
            raise ValueError(f".env.production file not found at {env_prod_path}")

        prod_env = dotenv_values(env_prod_path)
        prod_db_url = prod_env.get("DATABASE_URL")

        if not prod_db_url:
            raise ValueError("DATABASE_URL not found in .env.production file")

        logger.info("Dumping production database...")
        os.environ["DATABASE_URL"] = prod_db_url

        try:
            with open("prod_data.json", "w") as f:
                management.call_command(
                    "dumpdata",
                    "--natural-foreign",
                    "--natural-primary",
                    stdout=f,
                )
            logger.info("Production data exported")
        except Exception as e:
            raise RuntimeError(f"Failed to export production data: {e}") from e

        env_dev_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env.dev"
        if not env_dev_path.exists():
            raise ValueError(f".env.dev file not found at {env_dev_path}")

        dev_env = dotenv_values(env_dev_path)
        local_db_url = dev_env.get("DATABASE_URL")

        if not local_db_url:
            raise ValueError("DATABASE_URL not found in .env.dev file")

        logger.info("Loading data to local database...")
        os.environ["DATABASE_URL"] = local_db_url

        try:
            management.call_command("loaddata", "prod_data.json")
            logger.info("Production data loaded to local database")
        except Exception as e:
            raise RuntimeError(f"Failed to load data to local database: {e}") from e
        finally:
            if os.path.exists("prod_data.json"):
                os.remove("prod_data.json")
                logger.info("Cleaned up temporary prod_data.json file")

        logger.info("Database sync complete!")
