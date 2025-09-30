import json
import logging

from core.api.response_utils import ResponseStatus, create_response
from core.utils.redis_cache import CachePrefix, redis_cache_clear
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


def clear_redis_cache(request: HttpRequest) -> JsonResponse:
    """Clear Redis cache endpoint for ETL pipeline."""
    if request.method != "POST":
        return create_response(ResponseStatus.ERROR, "Method not allowed", None)

    try:
        body = json.loads(request.body) if request.body else {}
        cache_type = body.get("cache_type")

        if not cache_type:
            return create_response(ResponseStatus.ERROR, "cache_type is required", None)

        cache_prefix = CachePrefix(cache_type)
        cleared = redis_cache_clear(cache_prefix)
        logger.info(f"Cache cleared: {cleared} entries removed for {cache_type}")

        return create_response(
            ResponseStatus.SUCCESS,
            f"Cache cleared successfully: {cleared} entries removed",
            {"cleared_entries": cleared, "cache_type": cache_type},
        )

    except ValueError:
        valid_types = [prefix.value for prefix in CachePrefix]
        return create_response(
            ResponseStatus.ERROR, f"Invalid cache type: {cache_type}. Valid types: {valid_types}", None
        )
    except Exception as error:
        logger.error(f"Failed to clear cache: {error}")
        return create_response(ResponseStatus.ERROR, f"Failed to clear cache: {error}", None)
