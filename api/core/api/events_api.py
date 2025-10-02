import logging

import requests
from core.api.response_utils import ResponseStatus, create_response
from core.utils.cloudflare_cache import CloudflareKVCache
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)

EDM_EVENTS_GITHUB_URL = "https://raw.githubusercontent.com/AidanJaghab/Beatmap/main/backend/data/latest_events.json"
EDM_EVENTS_CACHE_KEY = "edm_events_data"

cache = None


def get_cache():
    global cache
    if cache is None:
        cache = CloudflareKVCache("", {})
    return cache


def get_edm_events(request: HttpRequest) -> JsonResponse:
    """Get EDM events data from GitHub with caching."""
    cached_data = get_cache().get(EDM_EVENTS_CACHE_KEY)
    if cached_data:
        logger.info("Returning cached EDM events data")
        return create_response(ResponseStatus.SUCCESS, "EDM events data retrieved from cache", cached_data)

    try:
        response = requests.get(EDM_EVENTS_GITHUB_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        get_cache().set(EDM_EVENTS_CACHE_KEY, data, timeout=3600)
        logger.info("EDM events data cached successfully")

        logger.info("EDM events data fetched successfully from GitHub")
        return create_response(ResponseStatus.SUCCESS, "EDM events data retrieved successfully", data)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch EDM events data: {e}")
        return create_response(ResponseStatus.ERROR, f"Failed to fetch EDM events: {e!s}", None)
    except Exception as error:
        logger.error(f"Unexpected error in get_edm_events: {error}")
        return create_response(ResponseStatus.ERROR, str(error), None)
