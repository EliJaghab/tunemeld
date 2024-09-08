import logging

logger = logging.getLogger(__name__)

class LogBadRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 400:
            logger.error(
                "400 Bad Request: %s %s\nHeaders: %s\nBody: %s",
                request.method,
                request.get_full_path(),
                request.headers,
                request.body,
            )
        return response