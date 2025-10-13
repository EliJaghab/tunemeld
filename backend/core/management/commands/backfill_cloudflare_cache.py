from typing import Any

import requests
from core.constants import DEV_ENV_PATH, PRODUCTION_ENV_PATH
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError
from dotenv import dotenv_values

logger = get_logger(__name__)


class CloudflareKVClient:
    """Simple CloudflareKV client for syncing caches."""

    def __init__(self, account_id: str, namespace_id: str, api_token: str):
        self.account_id = account_id
        self.namespace_id = namespace_id
        self.api_token = api_token
        self.base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces/{namespace_id}"
        )
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"})

    def list_keys(self, prefix: str | None = None, limit: int = 1000) -> list[dict[str, Any]]:
        """List all keys in the namespace, optionally filtered by prefix."""
        all_keys = []
        cursor = None

        while True:
            url = f"{self.base_url}/keys"
            params: dict[str, Any] = {"limit": limit}

            if prefix:
                params["prefix"] = prefix

            if cursor:
                params["cursor"] = cursor

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise ValueError(f"Cloudflare API error: {data}")

            result = data.get("result", [])
            all_keys.extend(result)

            result_info = data.get("result_info", {})
            cursor = result_info.get("cursor")

            if not cursor:
                break

        return all_keys

    def get(self, key: str) -> Any:
        """Get value for a key."""
        url = f"{self.base_url}/values/{key}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def set(self, key: str, value: str) -> bool:
        """Set value for a key."""
        url = f"{self.base_url}/values/{key}"
        response = self.session.put(url, data=value)
        response.raise_for_status()
        result = response.json()
        return result.get("success", False)


class Command(BaseCommand):
    help = "Backfill missing CloudflareKV cache keys from production to local (does not overwrite existing keys)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be backfilled without actually syncing",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get("dry_run", False)

        if not PRODUCTION_ENV_PATH.exists():
            raise ValueError(f".env.production file not found at {PRODUCTION_ENV_PATH}")

        prod_env = dotenv_values(PRODUCTION_ENV_PATH)
        prod_cf_account_id = prod_env.get("CF_ACCOUNT_ID")
        prod_cf_namespace_id = prod_env.get("CF_NAMESPACE_ID")
        prod_cf_api_token = prod_env.get("CF_API_TOKEN")

        if not all([prod_cf_account_id, prod_cf_namespace_id, prod_cf_api_token]):
            raise CommandError("Missing CloudflareKV credentials in .env.production")

        logger.info("Connecting to production CloudflareKV...")
        prod_client = CloudflareKVClient(
            account_id=str(prod_cf_account_id),
            namespace_id=str(prod_cf_namespace_id),
            api_token=str(prod_cf_api_token),
        )

        if not DEV_ENV_PATH.exists():
            raise ValueError(f".env.dev file not found at {DEV_ENV_PATH}")

        dev_env = dotenv_values(DEV_ENV_PATH)
        local_cf_account_id = dev_env.get("CF_ACCOUNT_ID")
        local_cf_namespace_id = dev_env.get("CF_NAMESPACE_ID")
        local_cf_api_token = dev_env.get("CF_API_TOKEN")

        if not all([local_cf_account_id, local_cf_namespace_id, local_cf_api_token]):
            raise CommandError("Missing CloudflareKV credentials in .env.dev")

        logger.info("Connecting to local CloudflareKV...")
        local_client = CloudflareKVClient(
            account_id=str(local_cf_account_id),
            namespace_id=str(local_cf_namespace_id),
            api_token=str(local_cf_api_token),
        )

        logger.info("Fetching production CloudflareKV keys...")
        prod_keys = prod_client.list_keys()

        total_keys = len(prod_keys)

        if total_keys == 0:
            logger.info("No keys found in production CloudflareKV")
            return

        logger.info(f"Found {total_keys} keys in production CloudflareKV")

        logger.info("Fetching local CloudflareKV keys to check for existing...")
        local_keys = local_client.list_keys()
        local_key_names = {key_info.get("name") for key_info in local_keys}
        logger.info(f"Local CloudflareKV has {len(local_key_names)} existing keys")

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info(f"\nAnalyzing {total_keys} keys:")

            missing_keys = []
            existing_keys = []

            for key_info in prod_keys:
                key_name = key_info.get("name")
                if not key_name:
                    continue

                if key_name in local_key_names:
                    existing_keys.append(key_name)
                else:
                    missing_keys.append(key_name)

            logger.info(f"\nMissing keys (would be backfilled): {len(missing_keys)}")
            logger.info(f"Existing keys (would be skipped): {len(existing_keys)}")

            return

        logger.info("Starting backfill of missing keys from production to local...")

        added_count = 0
        skipped_count = 0
        failed_count = 0

        for _i, key_info in enumerate(prod_keys, 1):
            key_name = key_info.get("name")

            if not key_name:
                logger.warning("Skipping key with missing name")
                failed_count += 1
                continue

            if key_name in local_key_names:
                skipped_count += 1
                continue

            try:
                value = prod_client.get(key_name)

                if not value:
                    logger.warning(f"Skipping key {key_name} (empty value)")
                    failed_count += 1
                    continue

                local_client.set(key_name, value)
                added_count += 1

                if added_count % 10 == 0:
                    logger.info(f"Added {added_count} keys (skipped {skipped_count} existing)...")

            except Exception as e:
                logger.error(f"Failed to sync key {key_name}: {e}")
                failed_count += 1

        logger.info("\nBackfill complete!")
        logger.info(f"  Added: {added_count} keys")
        logger.info(f"  Skipped (already exist): {skipped_count} keys")

        if failed_count > 0:
            logger.warning(f"  Failed: {failed_count} keys")
