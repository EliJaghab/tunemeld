"""FastAPI GraphQL endpoint using existing Django backend."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

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

# Import Django models and business logic
from core.graphql.schema import schema as django_schema


@strawberry.type
class TrackPlayCountType:
    """Track play count data."""
    isrc: str
    track_name: str
    artist_name: str
    album_name: Optional[str] = None
    spotify_url: Optional[str] = None
    tunemeld_rank: Optional[int] = None
    play_count: Optional[int] = None


@strawberry.type
class PlaylistType:
    """Playlist with tracks."""
    genre_name: str
    service_name: str
    tracks: List[TrackPlayCountType]


@strawberry.type
class Query:
    """GraphQL query root."""

    @strawberry.field
    def playlist(self, genre: str, service: str) -> Optional[PlaylistType]:
        """Get playlist by genre and service - reuses existing Django logic."""
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

            # Convert Django GraphQL response to FastAPI types
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
        return "Hello from FastAPI + Strawberry GraphQL!"


# Create FastAPI app
app = FastAPI(title="TuneMeld FastAPI GraphQL")

# Create GraphQL schema and router
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

# Add CORS headers
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# Vercel handler
handler = app