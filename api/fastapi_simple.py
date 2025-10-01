"""FastAPI endpoint using BaseHTTPRequestHandler pattern for Vercel compatibility."""

import json
from http.server import BaseHTTPRequestHandler
from io import StringIO


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Handler for FastAPI requests using Vercel-compatible pattern."""

    def do_GET(self):
        try:
            # Import FastAPI only when needed to avoid startup issues
            from fastapi import FastAPI

            app = FastAPI()

            @app.get("/")
            def read_root():
                return {"message": "Hello from FastAPI via BaseHTTPRequestHandler!", "status": "success"}

            @app.get("/health")
            def health_check():
                return {"status": "healthy", "framework": "FastAPI", "pattern": "BaseHTTPRequestHandler"}

            # Simple routing based on path
            if self.path == "/" or self.path == "":
                response_data = {"message": "Hello from FastAPI via BaseHTTPRequestHandler!", "status": "success"}
            elif self.path == "/health":
                response_data = {"status": "healthy", "framework": "FastAPI", "pattern": "BaseHTTPRequestHandler"}
            else:
                response_data = {"error": "Not found", "path": self.path}

            response = json.dumps(response_data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response.encode())

        except Exception as e:
            error_response = json.dumps({"error": f"FastAPI handler error: {e}"})
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error_response.encode())

    def do_POST(self):
        try:
            # For POST requests, could handle GraphQL here
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            response_data = {
                "message": "POST received",
                "data_length": content_length,
                "framework": "FastAPI",
                "method": "POST"
            }

            response = json.dumps(response_data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(response.encode())

        except Exception as e:
            error_response = json.dumps({"error": f"FastAPI POST handler error: {e}"})
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error_response.encode())