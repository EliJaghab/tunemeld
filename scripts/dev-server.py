#!/usr/bin/env python3
import http.server
import os
import socketserver


class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):  # noqa: N802
        # SPA fallback: serve index.html for all routes that don't correspond to actual files
        if not os.path.exists(self.translate_path(self.path)) and not self.path.startswith("/static/"):
            self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "docs"))
    port = 8080
    with socketserver.TCPServer(("", port), NoCacheHTTPRequestHandler) as httpd:
        print(f"Serving at http://localhost:{port}")
        print("Cache headers disabled for development")
        httpd.serve_forever()
