"""Test django_distill import for Vercel serverless function."""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Test django_distill import."""

    def do_GET(self):
        try:
            # Try to import django_distill
            import django_distill

            response = f"Successfully imported django_distill! Version: {getattr(django_distill, '__version__', 'unknown')}"
            status_code = 200
        except ImportError as e:
            response = f"Failed to import django_distill: {e!s}"
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))