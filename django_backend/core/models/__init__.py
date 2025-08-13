"""
TuneMeld Django Models - PostgreSQL ETL Pipeline

This package contains all Django models organized by ETL pipeline stage:

- base: Core lookup tables (Genre, Service)
- extract: Raw data models (RawPlaylistData, ETLRun)
- transform: Normalized data models (Track, TrackData, ViewCount)
- aggregate: Final output models (Playlist, TrackPlaylist)

All models use explicit BigAutoField primary keys and proper indexing
for PostgreSQL performance.
"""

# Base models (lookup tables)
# Aggregate phase models (final output)
from .aggregate import Playlist, PlaylistMetadata, TrackPlaylist
from .base import Genre, Service

# Extract phase models (raw data)
from .extract import ETLRun, RawPlaylistData

# Transform phase models (normalized data)
from .transform import HistoricalViewCount, Track, TrackData, ViewCount

__all__ = [
    "ETLRun",
    # Base
    "Genre",
    "HistoricalViewCount",
    # Aggregate
    "Playlist",
    "PlaylistMetadata",
    # Extract
    "RawPlaylistData",
    "Service",
    # Transform
    "Track",
    "TrackData",
    "TrackPlaylist",
    "ViewCount",
]
