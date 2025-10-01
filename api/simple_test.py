"""Extremely simple test function to verify basic Python runtime."""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Test basic Python functionality without Django imports."""

    def do_GET(self):
        try:
            # Test basic Python operations
            result = {"status": "success", "python_working": True}
            response = f"Basic Python test successful: {result}"

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
        except Exception as e:
            error_msg = f"Basic Python test failed: {e!s}"
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(error_msg.encode("utf-8"))
