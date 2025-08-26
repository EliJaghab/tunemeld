"""
Django cache backend for Cloudflare KV storage
"""

import json
import logging
import re
from typing import Any

from core.cache import Cache
from django.core.cache.backends.base import BaseCache

logger = logging.getLogger(__name__)


class CloudflareKVCache(BaseCache):
    """
    Django cache backend that uses Cloudflare KV for storage.

    This provides a simple read-through cache interface using your existing
    Cloudflare KV setup from core.cache.Cache.
    """

    def __init__(self, server, params):
        super().__init__(params)
        self.kv_client = Cache()

    def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        """Get value from cache"""
        key = self.make_key(key, version=version)
        self._validate_key(key)

        value = self.kv_client.get(key)
        if value is None:
            logger.info(f"Cache MISS: {key}")
            return default

        result = json.loads(value)
        logger.info(f"Cache HIT: {key}")
        return result

    def set(self, key: str, value: Any, timeout: int | None = None, version: int | None = None) -> bool:
        """Set value in cache"""
        key = self.make_key(key, version=version)
        self._validate_key(key)

        serialized_value = json.dumps(value)
        result = self.kv_client.put(key, serialized_value)
        success = result.get("success", False)
        if success:
            logger.info(f"Cache SET: {key}")
        else:
            logger.warning(f"Cache SET FAILED: {key}")
        return success

    def delete(self, key: str, version: int | None = None) -> bool:
        """Delete value from cache (not supported by KV, returns True)"""
        return self.set(key, None, version=version)

    def clear(self) -> bool:
        """Clear all cache (not supported by KV, returns True)"""
        logger.info("Cache cleared (KV doesn't support bulk delete)")
        return True

    def has_key(self, key: str, version: int | None = None) -> bool:
        """Check if key exists in cache"""
        return self.get(key, version=version) is not None

    def _validate_key(self, key: str) -> None:
        """
        Validate cache key is compatible with Cloudflare KV.

        KV key restrictions:
        - Max 512 characters
        - Only alphanumeric, hyphens, underscores
        - Cannot be empty

        Raises ValueError if key is invalid.
        """
        if not key:
            raise ValueError("Cache key cannot be empty")

        if len(key) > 512:
            raise ValueError(f"Cache key too long: {len(key)} chars (max 512)")

        if not re.match(r"^[\w\-]+$", key):
            raise ValueError(f"Cache key contains invalid characters: {key}")

        if key.startswith("-") or key.endswith("-"):
            raise ValueError(f"Cache key cannot start/end with hyphen: {key}")

        if "__" in key:
            raise ValueError(f"Cache key cannot contain consecutive underscores: {key}")
