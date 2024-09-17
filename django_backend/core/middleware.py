import logging
import traceback

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"Request: {request.method} {request.path}")
        try:
            response = self.get_response(request)
        except Exception as e:
            logger.exception("Exception during request processing")
            raise 
        if response.status_code >= 400:
            logger.error(
                f"Response: {response.status_code} {response.reason_phrase} "
                f"for {request.method} {request.path}"
            )
        else:
            logger.info(
                f"Response: {response.status_code} {response.reason_phrase} "
                f"for {request.method} {request.path}"
            )
        return response
