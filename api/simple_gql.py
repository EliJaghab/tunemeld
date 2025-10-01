"""Simple GraphQL endpoint that fixes Django issues without complex dependencies."""

import json
import os
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Initialize Django (same pattern as existing api/index.py)
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Simple approach: try to import and setup Django, catch any reentrant errors
try:
    import django
    from django.conf import settings

    if not settings.configured:
        django.setup()
except Exception:
    # If Django setup fails, we'll handle it in the request
    pass

# Import the existing Django GraphQL schema
try:
    from core.graphql.schema import schema as django_schema
    SCHEMA_AVAILABLE = True
except Exception:
    SCHEMA_AVAILABLE = False
    django_schema = None


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Simple GraphQL handler that fixes Django reentrant issues."""

    def _handle_graphql(self, query, variables=None):
        """Handle GraphQL query execution using existing Django schema."""
        if not SCHEMA_AVAILABLE:
            return {"errors": ["GraphQL schema not available"]}

        try:
            # Use the existing Django GraphQL schema
            result = django_schema.execute(query, variables=variables)

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
                # Return a simple health check if no query
                response = {"message": "Simple GraphQL endpoint is working!", "status": "success"}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
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