"""Vercel serverless entry point that wraps Django WSGI in BaseHTTPRequestHandler."""

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

app = get_wsgi_application()


class handler(BaseHTTPRequestHandler):  # noqa: N801
    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_OPTIONS(self):
        self._handle_request()

    def _handle_request(self):
        # Create WSGI environ from HTTP request
        environ = {
            "REQUEST_METHOD": self.command,
            "PATH_INFO": urlparse(self.path).path,
            "QUERY_STRING": urlparse(self.path).query or "",
            "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": self.headers.get("Content-Length", ""),
            "SERVER_NAME": self.headers.get("Host", "").split(":")[0],
            "SERVER_PORT": "443",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "https",
            "wsgi.input": StringIO(),
            "wsgi.errors": StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }

        # Add HTTP headers to environ
        for header, value in self.headers.items():
            header = header.replace("-", "_").upper()
            if header not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                environ[f"HTTP_{header}"] = value

        # Read request body for POST requests
        if self.command == "POST":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                environ["wsgi.input"] = StringIO(body.decode("utf-8"))

        # Capture response
        status = None
        headers = []

        def start_response(status_line, response_headers):
            nonlocal status, headers
            status = int(status_line.split(" ")[0])
            headers = response_headers

        # Call Django WSGI app
        response = app(environ, start_response)

        # Send HTTP response
        self.send_response(status)
        for header, value in headers:
            self.send_header(header, value)
        self.end_headers()

        # Write response body
        for chunk in response:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            self.wfile.write(chunk)
