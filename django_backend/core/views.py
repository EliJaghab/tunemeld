import logging
from enum import Enum

import requests
from django.http import JsonResponse

EDM_EVENTS_GITHUB_URL = "https://raw.githubusercontent.com/AidanJaghab/Beatmap/main/backend/data/latest_events.json"
EDM_EVENTS_CACHE_KEY = "edm_events_data"

# Safe cache import with fallback
try:
    from core.cache import Cache

    cache = Cache()
except Exception:
    cache = None


logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"


def create_response(status: ResponseStatus, message: str, data: dict | list | None) -> JsonResponse:
    """Create a standardized JSON response."""
    return JsonResponse(
        {
            "status": status.value,
            "message": message,
            "data": data,
        }
    )


def root(request):
    """Root endpoint - returns basic API information."""
    return create_response(
        ResponseStatus.SUCCESS,
        "TuneMeld API is running",
        {
            "version": "1.0.0",
            "endpoints": [
                "/health/",
                "/edm-events/",
                "/gql/",
            ],
        },
    )


def health(request):
    """Health check endpoint."""
    return create_response(ResponseStatus.SUCCESS, "Service is healthy", {"status": "ok"})


def get_edm_events(request):
    """Get EDM events data from GitHub with caching."""
    if cache:
        cached_data = cache.get(EDM_EVENTS_CACHE_KEY)
        if cached_data:
            logger.info("Returning cached EDM events data")
            return create_response(ResponseStatus.SUCCESS, "EDM events data retrieved from cache", cached_data)

    try:
        response = requests.get(EDM_EVENTS_GITHUB_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        if cache:
            cache.put(EDM_EVENTS_CACHE_KEY, data, ttl=3600)  # 1 hour TTL
            logger.info("EDM events data cached successfully")

        logger.info("EDM events data fetched successfully from GitHub")
        return create_response(ResponseStatus.SUCCESS, "EDM events data retrieved successfully", data)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch EDM events data: {e}")
        return create_response(ResponseStatus.ERROR, f"Failed to fetch EDM events: {e!s}", None)
    except Exception as error:
        logger.error(f"Unexpected error in get_edm_events: {error}")
        return create_response(ResponseStatus.ERROR, str(error), None)
