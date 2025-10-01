#!/usr/bin/env python3
"""Local test server for GraphQL handler that mirrors Vercel serverless function behavior."""

from http.server import HTTPServer

from api.index import handler


def test_handler_locally():
    """Start a local server to test the GraphQL handler."""
    server_address = ("localhost", 8001)

    print("Starting local test server at http://localhost:8001")
    print("Test URLs:")
    print("  GET:  http://localhost:8001/?query={__schema{types{name}}}")
    print(
        "  POST: curl -X POST http://localhost:8001 -H 'Content-Type: application/json' -d '{\"query\":\"{__schema{types{name}}}\"}'"
    )
    print("\nPress Ctrl+C to stop the server")

    httpd = HTTPServer(server_address, handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == "__main__":
    test_handler_locally()
