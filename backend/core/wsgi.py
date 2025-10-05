import json
import os
import sys
import traceback

from django.core.wsgi import get_wsgi_application

# Add the backend directory to Python path for Vercel
backend_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


def error_application(environ, start_response):
    """Fallback WSGI app that returns startup errors."""
    status = "500 Internal Server Error"
    headers = [("Content-type", "application/json")]
    start_response(status, headers)

    error_response = json.dumps(
        {"error": "WSGI APPLICATION FAILED TO START", "details": "Check Vercel function logs for details"}
    )
    return [error_response.encode()]


try:
    # Vercel expects the WSGI application to be named 'app'
    app = get_wsgi_application()
    # Keep backward compatibility
    application = app

except Exception as e:
    # Print to stderr for Vercel logs
    print(f"ERROR: WSGI APPLICATION FAILED TO START: {e!s}", file=sys.stderr)
    print(f"TRACEBACK:\n{traceback.format_exc()}", file=sys.stderr)

    app = error_application
    application = error_application
