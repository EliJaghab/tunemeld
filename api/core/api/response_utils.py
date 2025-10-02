from enum import Enum

from django.http import JsonResponse


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
