"""Test Django imports for Vercel serverless function."""

import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Test Django imports step by step."""

    def do_GET(self):
        try:
            # Step 1: Add backend to path
            backend_dir = Path(__file__).parent.parent / "backend"
            sys.path.insert(0, str(backend_dir))

            # Step 2: Set Django settings
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

            # Step 3: Test Django import
            try:
                import django

                django_version = django.get_version()
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Django import failed: {e}".encode())
                return

            # Step 4: Test Django setup
            try:
                django.setup()
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Django setup failed: {e}".encode())
                return

            # Step 5: Test schema import
            try:
                from core.graphql.schema import schema

                schema_type = str(type(schema))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Schema import failed: {e}".encode())
                return

            # Success!
            response = f"SUCCESS! Django {django_version}, Schema: {schema_type}"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"General error: {e}".encode())
