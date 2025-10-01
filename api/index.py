"""Vercel serverless entry point for Django GraphQL endpoint."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Handler for Django GraphQL requests."""

    def _setup_django(self):
        """Initialize Django setup."""
        try:
            # Add backend directory to Python path
            backend_dir = Path(__file__).parent.parent / "backend"
            sys.path.insert(0, str(backend_dir))

            # Set Django settings
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

            import django

            django.setup()

            from core.schema import schema

            return schema
        except Exception as e:
            raise Exception(f"Django setup failed: {e}") from e

    def _handle_graphql(self, query, variables=None):
        """Handle GraphQL query execution."""
        try:
            schema = self._setup_django()
            result = schema.execute(query, variables=variables)

            response_data = {"data": result.data}
            if result.errors:
                response_data["errors"] = [str(error) for error in result.errors]

            return response_data
        except Exception as e:
            return {"errors": [f"GraphQL execution failed: {e}"]}

    def do_GET(self):
        """Handle GET request for GraphQL endpoint."""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            query = query_params.get("query", [None])[0]
            if not query:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing query parameter"}).encode())
                return

            variables = query_params.get("variables", [None])[0]
            if variables:
                variables = json.loads(variables)

            result = self._handle_graphql(query, variables)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_response = {"errors": [f"Server error: {e}"]}
            self.wfile.write(json.dumps(error_response).encode())

    def do_POST(self):
        """Handle POST request for GraphQL endpoint."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                request_data = json.loads(post_data.decode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
                return

            query = request_data.get("query")
            variables = request_data.get("variables")

            if not query:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing query"}).encode())
                return

            result = self._handle_graphql(query, variables)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_response = {"errors": [f"Server error: {e}"]}
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
