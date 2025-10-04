import os
import sys
import traceback
from pathlib import Path

try:
    from django.core.wsgi import get_wsgi_application

    # Add the backend directory to Python path for Vercel
    current_path = Path(__file__).parent
    backend_path = current_path.parent
    sys.path.insert(0, str(backend_path))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    # Vercel expects the WSGI application to be named 'app'
    app = get_wsgi_application()

    # Keep backward compatibility
    application = app

except Exception as e:
    # Capture and log the actual error for debugging
    error_msg = f"WSGI APPLICATION FAILED TO START: {e!s}"
    error_traceback = traceback.format_exc()

    # Print to stderr for Vercel logs
    print(f"ERROR: {error_msg}", file=sys.stderr)
    print(f"TRACEBACK:\n{error_traceback}", file=sys.stderr)

    # Also print environment info for debugging
    print("ENVIRONMENT VARIABLES:", file=sys.stderr)
    for key in sorted(os.environ.keys()):
        if any(secret in key.lower() for secret in ["secret", "password", "token", "key"]):
            print(f"  {key}=***REDACTED***", file=sys.stderr)
        else:
            print(f"  {key}={os.environ[key]}", file=sys.stderr)

    print(f"PYTHON PATH: {sys.path}", file=sys.stderr)
    print(f"CURRENT DIR: {os.getcwd()}", file=sys.stderr)

    # Create a fallback WSGI app that returns the error
    def error_application(environ, start_response):
        status = "500 Internal Server Error"
        headers = [("Content-type", "application/json")]
        start_response(status, headers)
        import json

        error_response = json.dumps({"error": error_msg, "traceback": error_traceback})
        return [error_response.encode()]

    app = error_application
    application = error_application
