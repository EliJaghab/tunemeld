from core.api.response_utils import ResponseStatus, create_response
from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
    """Health check endpoint."""
    return create_response(ResponseStatus.SUCCESS, "Service is healthy", {"status": "ok"})


def root(request: HttpRequest) -> JsonResponse:
    """Root endpoint - returns basic API information."""
    return create_response(
        ResponseStatus.SUCCESS,
        "TuneMeld API is running",
        {
            "version": "1.0.0",
            "endpoints": [
                "/health/",
                "/edm-events/",
                "/clear-local-cache/",
                "/gql/",
            ],
        },
    )
