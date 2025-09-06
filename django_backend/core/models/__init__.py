from core.models.b_genre_service import Genre, Service
from core.models.d_raw_playlist import RawPlaylistData
from core.models.e_playlist import Playlist as PlaylistModel
from core.models.e_playlist import ServiceTrack

# Import ETL Pydantic models for backward compatibility
from core.models.f_etl_types import (
    CurrentView,
    DataSourceServiceName,
    ETLTrack,
    HistoricalView,
    NormalizedTrack,
    Playlist,
    PlaylistType,
    ServiceView,
    StartView,
    TrackData,
    TrackRank,
    TrackSourceServiceName,
    YouTubeView,
)
from core.models.f_track import Track
from core.models.view_counts import HistoricalViewCount, ViewCount

__all__ = [
    "CurrentView",
    "DataSourceServiceName",
    "ETLTrack",
    "Genre",
    "HistoricalView",
    "HistoricalViewCount",
    "NormalizedTrack",
    "Playlist",
    "PlaylistModel",
    "PlaylistType",
    "RawPlaylistData",
    "Service",
    "ServiceTrack",
    "ServiceView",
    "StartView",
    "Track",
    "TrackData",
    "TrackRank",
    "TrackSourceServiceName",
    "ViewCount",
    "YouTubeView",
]
