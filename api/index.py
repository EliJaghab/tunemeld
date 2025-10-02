import os
import sys
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote

import django
from django.core.wsgi import get_wsgi_application

# Add the backend directory to Python path
current_path = Path(__file__).parent
backend_path = current_path / "backend"
sys.path.insert(0, str(backend_path))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Initialize Django
django.setup()

# Get WSGI application
app = get_wsgi_application()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        return self.handle_request()

    def do_POST(self):
        return self.handle_request()

    def do_PUT(self):
        return self.handle_request()

    def do_DELETE(self):
        return self.handle_request()

    def do_PATCH(self):
        return self.handle_request()

    def do_OPTIONS(self):
        return self.handle_request()

    def handle_request(self):
        # Build the environ dict for WSGI
        environ = {
            "REQUEST_METHOD": self.command,
            "SCRIPT_NAME": "",
            "PATH_INFO": unquote(self.path.split("?")[0]),
            "QUERY_STRING": self.path.split("?")[1] if "?" in self.path else "",
            "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": self.headers.get("Content-Length", ""),
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": BytesIO(self.rfile.read(int(self.headers.get("Content-Length", 0)))),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }

        # Add headers to environ
        for key, value in self.headers.items():
            key = key.replace("-", "_").upper()
            if key not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                key = f"HTTP_{key}"
            environ[key] = value

        # Capture response
        response_status = [None]
        response_headers = []

        def start_response(status, headers, exc_info=None):
            response_status[0] = status
            response_headers[:] = headers

        # Call Django app
        response = app(environ, start_response)

        # Send response
        status_code = int(response_status[0].split(" ", 1)[0])
        self.send_response(status_code)

        for header_name, header_value in response_headers:
            self.send_header(header_name, header_value)
        self.end_headers()

        # Write response body
        for data in response:
            if isinstance(data, str):
                data = data.encode("utf-8")
            self.wfile.write(data)


# Export the handler for Vercel
handler = Handler
