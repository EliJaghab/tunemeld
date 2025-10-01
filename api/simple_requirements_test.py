"""Test Python function with a simple dependency to verify Vercel installs packages."""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Test Python function that tries to import a simple package."""

    def do_GET(self):
        try:
            # Try to import a simple package that's in requirements.txt
            import requests

            response = f"Successfully imported requests! Version: {requests.__version__}"
            status_code = 200
        except ImportError as e:
            response = f"Failed to import requests: {e!s}"
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))
