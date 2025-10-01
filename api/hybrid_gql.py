"""Hybrid GraphQL endpoint: Django handler pattern with Strawberry GraphQL for performance."""

import json
import os
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from typing import List, Optional

# Initialize Django (same pattern as existing api/index.py)
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
from django.conf import settings

# Setup Django, handling reentrant setup gracefully
try:
    if not settings.configured:
        django.setup()
except RuntimeError as e:
    if "populate() isn't reentrant" in str(e):
        # Django is already configured, continue
        pass
    else:
        raise

# Now import Strawberry and create the schema
import strawberry

# Import Django models and business logic
from core.graphql.schema import schema as django_schema


@strawberry.type
class TrackPlayCountType:
    """Track play count data using Strawberry."""
    isrc: str
    track_name: str
    artist_name: str
    album_name: Optional[str] = None
    spotify_url: Optional[str] = None
    tunemeld_rank: Optional[int] = None
    play_count: Optional[int] = None


@strawberry.type
class PlaylistType:
    """Playlist with tracks using Strawberry."""
    genre_name: str
    service_name: str
    tracks: List[TrackPlayCountType]


@strawberry.type
class Query:
    """GraphQL query root using Strawberry."""

    @strawberry.field
    def playlist(self, genre: str, service: str) -> Optional[PlaylistType]:
        """Get playlist by genre and service - reuses existing Django logic but with Strawberry."""
        try:
            # Execute the same query through Django's GraphQL schema
            query = """
            query GetPlaylist($genre: String!, $service: String!) {
                playlist(genre: $genre, service: $service) {
                    genreName
                    serviceName
                    tracks {
                        isrc
                        trackName
                        artistName
                        albumName
                        spotifyUrl
                        tunemeldRank
                        playCount
                    }
                }
            }
            """

            result = django_schema.execute(query, variables={"genre": genre, "service": service})

            if result.errors:
                return None

            if not result.data or not result.data.get("playlist"):
                return None

            playlist_data = result.data["playlist"]

            # Convert Django GraphQL response to Strawberry types
            tracks = [
                TrackPlayCountType(
                    isrc=track["isrc"],
                    track_name=track["trackName"],
                    artist_name=track["artistName"],
                    album_name=track.get("albumName"),
                    spotify_url=track.get("spotifyUrl"),
                    tunemeld_rank=track.get("tunemeldRank"),
                    play_count=track.get("playCount")
                )
                for track in playlist_data["tracks"]
            ]

            return PlaylistType(
                genre_name=playlist_data["genreName"],
                service_name=playlist_data["serviceName"],
                tracks=tracks
            )

        except Exception:
            return None

    @strawberry.field
    def hello(self) -> str:
        """Simple health check."""
        return "Hello from Hybrid Django + Strawberry GraphQL!"


# Create Strawberry schema
strawberry_schema = strawberry.Schema(query=Query)


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Handler for hybrid GraphQL requests using Django pattern but Strawberry processing."""

    def _handle_graphql(self, query, variables=None):
        """Handle GraphQL query execution using Strawberry."""
        try:
            # Use Strawberry schema instead of Django's Graphene schema
            result = strawberry_schema.execute_sync(query, variables)

            response_data = {"data": result.data}
            if result.errors:
                response_data["errors"] = [str(error) for error in result.errors]

            return response_data
        except Exception as e:
            return {"errors": [f"Strawberry GraphQL execution failed: {e}"]}

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