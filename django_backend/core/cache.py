import json
import logging
import os
import re
from typing import Any

import requests
from core import settings
from core.settings import DEV
from django.core.cache.backends.base import BaseCache

logger = logging.getLogger(__name__)


class Cache(BaseCache):
    BASE_URL_TEMPLATE = "https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces/{}/values/"
    _session: requests.Session | None = None

    def __init__(self, server, params):
        super().__init__(params)
        logger.debug("Initializing Cache class...")

        self.CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID or ""
        self.CF_NAMESPACE_ID = settings.CF_NAMESPACE_ID or ""
        self.CF_API_TOKEN = settings.CF_API_TOKEN or ""

        if Cache._session is None:
            Cache._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=0)
            Cache._session.mount("https://", adapter)
            Cache._session.headers.update(
                {"Authorization": f"Bearer {self.CF_API_TOKEN}", "Content-Type": "application/json"}
            )

        # Allow cache to be initialized without credentials in CI/test environments
        secret_key = getattr(settings, "SECRET_KEY", os.getenv("SECRET_KEY", ""))
        is_ci = (
            secret_key == "test-secret-key-for-ci"
            or getattr(settings, "TESTING", False)
            or os.getenv("CI", "").lower() == "true"
        )
        logger.debug(f"Cache init: SECRET_KEY={secret_key}, is_ci={is_ci}")

        if not self.CF_ACCOUNT_ID or not self.CF_NAMESPACE_ID or not self.CF_API_TOKEN:
            if is_ci:
                logger.warning("Cache initialized without Cloudflare KV credentials (CI/test environment)")
                self.BASE_URL = ""
                return
            else:
                missing = []
                if not self.CF_ACCOUNT_ID:
                    missing.append("CF_ACCOUNT_ID")
                if not self.CF_NAMESPACE_ID:
                    missing.append("CF_NAMESPACE_ID")
                if not self.CF_API_TOKEN:
                    missing.append("CF_API_TOKEN")
                raise ValueError(f"Missing required Cloudflare KV credentials: {', '.join(missing)}")

        self.BASE_URL = self.BASE_URL_TEMPLATE.format(self.CF_ACCOUNT_ID, self.CF_NAMESPACE_ID)
        logger.info("Cache initialized with Cloudflare KV + shared connection pool")

    def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        if settings.ENVIRONMENT == DEV:
            return default

        key = self.make_key(key, version=version)
        sanitized_key = self._validate_key(key)

        if not self.BASE_URL:
            return default

        try:
            url = self.BASE_URL + sanitized_key
            if Cache._session is None:
                return default
            response = Cache._session.get(url)
            value = response.json().get("value")
            return json.loads(value) if value else default
        except Exception as e:
            logger.warning(f"Error getting key {key}: {e}")
            return default

    def set(self, key: str, value: Any, timeout: int | None = None, version: int | None = None) -> bool:
        if settings.ENVIRONMENT == DEV:
            return True

        key = self.make_key(key, version=version)
        sanitized_key = self._validate_key(key)

        if not self.BASE_URL:
            return False

        try:
            url = self.BASE_URL + sanitized_key
            serialized_value = json.dumps(value)
            if Cache._session is None:
                return False
            response = Cache._session.put(url, json={"value": serialized_value})
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except Exception as e:
            logger.warning(f"Error setting key {key}: {e}")
            return False

    def put(self, key, value):
        return self.set(key, value)

    def delete(self, key: str, version: int | None = None) -> bool:
        return self.set(key, None, version=version)

    def clear(self) -> bool:
        return True

    def has_key(self, key: str, version: int | None = None) -> bool:
        return self.get(key, version=version) is not None

    def _validate_key(self, key: str) -> str:
        sanitized_key = re.sub(r"[^a-zA-Z0-9\-_]", "_", key)
        return sanitized_key[:512] if len(sanitized_key) > 512 else sanitized_key
