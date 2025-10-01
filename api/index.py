"""Vercel serverless entry point for Django WSGI application."""

import os
import sys
from http.server import BaseHTTPRequestHandler
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

# Get Django WSGI application
wsgi_app = get_wsgi_application()


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Vercel serverless function handler for Django."""

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_DELETE(self):
        self._handle_request()

    def do_PATCH(self):
        self._handle_request()

    def do_HEAD(self):
        self._handle_request()

    def do_OPTIONS(self):
        self._handle_request()

    def _handle_request(self):
        """Handle HTTP request through Django WSGI."""
        # Parse URL
        parsed_url = urlparse(self.path)

        # Build WSGI environ
        environ = {
            "REQUEST_METHOD": self.command,
            "SCRIPT_NAME": "",
            "PATH_INFO": parsed_url.path,
            "QUERY_STRING": parsed_url.query,
            "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": self.headers.get("Content-Length", ""),
            "SERVER_NAME": self.headers.get("Host", "localhost").split(":")[0],
            "SERVER_PORT": "443",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "https",
            "wsgi.input": StringIO(),
            "wsgi.errors": StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }

        # Add headers to environ
        for key, value in self.headers.items():
            key = key.replace("-", "_").upper()
            if key not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                key = "HTTP_" + key
            environ[key] = value

        # Handle request body for POST/PUT requests
        if self.command in ("POST", "PUT", "PATCH"):
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                environ["wsgi.input"] = StringIO(body.decode("utf-8"))

        # Response data
        status = None
        headers = []

        def start_response(status_line, response_headers, exc_info=None):
            nonlocal status, headers
            status = status_line
            headers = response_headers

        # Call Django WSGI app
        response = wsgi_app(environ, start_response)

        # Send response
        status_code = int(status.split(" ", 1)[0])
        self.send_response(status_code)

        for header_name, header_value in headers:
            self.send_header(header_name, header_value)
        self.end_headers()

        # Write response body
        for data in response:
            if isinstance(data, str):
                data = data.encode("utf-8")
            self.wfile.write(data)
