import logging
from enum import Enum

from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"


def create_response(status: ResponseStatus, message: str, data=None):
    return JsonResponse({"status": status.value, "message": message, "data": data})


def success_response(data, message="Success"):
    return create_response(ResponseStatus.SUCCESS, message, data)


def error_response(message, status=400):
    return JsonResponse({"status": ResponseStatus.ERROR.value, "message": message, "data": None}, status=status)
