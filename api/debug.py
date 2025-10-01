"""Debug function to test Django imports in Vercel."""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Test Django imports step by step."""

    def do_GET(self):
        try:
            import os
            import sys
            from pathlib import Path

            # Add backend directory to Python path
            backend_dir = Path(__file__).parent.parent / "backend"
            sys.path.insert(0, str(backend_dir))

            # Set Django settings
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

            try:
                import django

                django.setup()
                response = f"Django setup successful! Version: {django.get_version()}"
                status_code = 200
            except Exception as e:
                response = f"Django setup failed: {e!s}"
                status_code = 500

        except Exception as e:
            response = f"Basic imports failed: {e!s}"
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))
