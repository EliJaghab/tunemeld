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


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "docs"))
    port = 8080
    with socketserver.TCPServer(("", port), NoCacheHTTPRequestHandler) as httpd:
        print(f"Serving at http://localhost:{port}")
        print("Cache headers disabled for development")
        httpd.serve_forever()
