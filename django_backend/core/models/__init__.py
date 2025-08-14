"""
TuneMeld Django Models - PostgreSQL ETL Pipeline

This package contains all Django models organized by letter-prefixed ETL pipeline stages:

- a_lookup_tables: Core lookup tables (Genre, Service)
- b_raw_data: Raw data models (RawPlaylistData)
- c_playlist_track: Normalized playlist track data (PlaylistTrack)
- e_aggregate: Final aggregate models (Playlist, TrackPlaylist, PlaylistMetadata)
- Legacy files for remaining models: transform

All models use explicit BigAutoField primary keys and proper indexing
for PostgreSQL performance.
"""

# Phase 1: Lookup tables
from core.models.a_lookup_tables import Genre, Service

# Phase 2: Raw data storage
from core.models.b_raw_data import RawPlaylistData

# Phase 3: Normalized playlist tracks
from core.models.c_playlist_track import PlaylistTrack

# Phase 5: Aggregate models
from core.models.e_aggregate import Playlist, PlaylistMetadata, TrackPlaylist

# Legacy transform phase models
from core.models.transform import HistoricalViewCount, Track, TrackData, ViewCount

__all__ = [
    # Phase 1
    "Genre",
    # Legacy transform
    "HistoricalViewCount",
    # Phase 5
    "Playlist",
    "PlaylistMetadata",
    # Phase 3
    "PlaylistTrack",
    # Phase 2
    "RawPlaylistData",
    "Service",
    "Track",
    "TrackData",
    "TrackPlaylist",
    "ViewCount",
]
