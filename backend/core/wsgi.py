import json
import os
import sys
import traceback
from datetime import datetime

# Add the backend directory to Python path for Vercel
backend_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Enhanced startup logging
print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Python {sys.version}", file=sys.stderr)
settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
print(
    f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: DJANGO_SETTINGS_MODULE = {settings_module}",
    file=sys.stderr,
)
print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Backend path = {backend_path}", file=sys.stderr)
print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Python path = {sys.path[:3]}", file=sys.stderr)

try:
    print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Importing Django WSGI...", file=sys.stderr)
    from django.core.wsgi import get_wsgi_application

    print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Django import successful", file=sys.stderr)
except Exception as e:
    print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: FAILED to import Django: {e}", file=sys.stderr)
    raise


def error_application(environ, start_response):
    """Fallback WSGI app that returns startup errors."""
    path_info = environ.get("PATH_INFO", "unknown")
    print(
        f"[{datetime.utcnow().isoformat()}] ERROR_APPLICATION: Handling request to {path_info}",
        file=sys.stderr,
    )
    status = "500 Internal Server Error"
    headers = [("Content-type", "application/json"), ("Access-Control-Allow-Origin", "*")]
    start_response(status, headers)

    error_response = json.dumps(
        {
            "error": "WSGI APPLICATION FAILED TO START",
            "details": "Check Vercel function logs for details",
            "path": environ.get("PATH_INFO", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    return [error_response.encode()]


try:
    print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Calling get_wsgi_application()...", file=sys.stderr)
    # Vercel expects the WSGI application to be named 'app'
    app = get_wsgi_application()
    print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: SUCCESS! Django WSGI application created", file=sys.stderr)
    # Keep backward compatibility
    application = app

except Exception as e:
    # Print to stderr for Vercel logs
    print(f"[{datetime.utcnow().isoformat()}] ERROR: WSGI APPLICATION FAILED TO START: {e!s}", file=sys.stderr)
    print(f"[{datetime.utcnow().isoformat()}] TRACEBACK:\n{traceback.format_exc()}", file=sys.stderr)
    print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Using error_application fallback", file=sys.stderr)

    app = error_application
    application = error_application

print(f"[{datetime.utcnow().isoformat()}] WSGI STARTUP: Module loaded, app = {type(app)}", file=sys.stderr)
