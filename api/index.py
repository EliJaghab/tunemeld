import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

import django
from django.core.wsgi import get_wsgi_application

# Add the current directory to Python path
current_path = Path(__file__).parent
sys.path.insert(0, str(current_path))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Initialize Django
django.setup()

# Get the WSGI application
application = get_wsgi_application()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Create a simple WSGI environ dict
            environ = {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": unquote(self.path),
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "CONTENT_TYPE": "",
                "CONTENT_LENGTH": "",
                "wsgi.version": (1, 0),
                "wsgi.url_scheme": "https",
                "wsgi.input": None,
                "wsgi.errors": sys.stderr,
                "wsgi.multithread": False,
                "wsgi.multiprocess": True,
                "wsgi.run_once": False,
            }

            # Add headers to environ
            for header, value in self.headers.items():
                key = "HTTP_{}".format(header.upper().replace("-", "_"))
                environ[key] = value

            # Capture response
            status = [None]
            headers = [None]

            def start_response(status_string, response_headers):
                status[0] = int(status_string.split(" ", 1)[0])
                headers[0] = dict(response_headers)

            # Call Django application
            response = application(environ, start_response)

            # Send response
            self.send_response(status[0] or 200)
            if headers[0]:
                for header, value in headers[0].items():
                    self.send_header(header, value)
            self.end_headers()

            # Write response body
            for chunk in response:
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                self.wfile.write(chunk)

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {e!s}".encode())

    def do_POST(self):
        self.do_GET()  # Handle POST same as GET for now


# Create alias for Vercel
handler = Handler
