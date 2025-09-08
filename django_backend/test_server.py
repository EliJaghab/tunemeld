#!/usr/bin/env python3
"""Minimal test server to verify Railway can run Python"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "success",
                "message": "Test server running - Django not loaded yet",
                "python": sys.version,
                "env": {
                    "RAILWAY_ENVIRONMENT": os.environ.get("RAILWAY_ENVIRONMENT", "not set"),
                    "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE", "not set"),
                    "SECRET_KEY": "set" if os.environ.get("SECRET_KEY") else "not set",
                },
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = 8000
    print(f"Starting test server on port {port}")
    server = HTTPServer(("0.0.0.0", port), TestHandler)
    server.serve_forever()
