"""Debug path resolution in Vercel serverless function."""

import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Debug path and file system access in Vercel."""

    def do_GET(self):
        try:
            debug_info = []

            # Current working directory
            cwd = os.getcwd()
            debug_info.append(f"CWD: {cwd}")

            # Script location
            script_path = Path(__file__)
            debug_info.append(f"Script: {script_path}")
            debug_info.append(f"Script parent: {script_path.parent}")
            debug_info.append(f"Script parent.parent: {script_path.parent.parent}")

            # Check if backend directory exists
            backend_dir = script_path.parent.parent / "backend"
            debug_info.append(f"Backend dir: {backend_dir}")
            debug_info.append(f"Backend exists: {backend_dir.exists()}")

            if backend_dir.exists():
                # List contents of backend directory
                try:
                    backend_contents = list(backend_dir.iterdir())
                    debug_info.append(f"Backend contents: {[p.name for p in backend_contents]}")

                    # Check for core directory
                    core_dir = backend_dir / "core"
                    debug_info.append(f"Core dir: {core_dir}")
                    debug_info.append(f"Core exists: {core_dir.exists()}")

                    if core_dir.exists():
                        core_contents = list(core_dir.iterdir())
                        debug_info.append(f"Core contents: {[p.name for p in core_contents]}")
                except Exception as e:
                    debug_info.append(f"Error listing backend: {e}")

            # Current Python path
            debug_info.append(f"Python path: {sys.path[:5]}...")

            # Try to list current directory
            try:
                current_contents = list(Path(".").iterdir())
                debug_info.append(f"Current dir contents: {[p.name for p in current_contents]}")
            except Exception as e:
                debug_info.append(f"Error listing current: {e}")

            response = "\n".join(debug_info)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Debug error: {e}".encode())
