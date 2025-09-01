"""
Phase F: ETL Pydantic Models for Legacy Integration

These models support the legacy playlist ETL pipeline.
They are Pydantic models (not Django models) for data validation and serialization.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from playlist_etl.constants import GenreName, ServiceName

# Backward compatibility aliases
TrackSourceServiceName = ServiceName


class DataSourceServiceName(str, Enum):
    SPOTIFY = TrackSourceServiceName.SPOTIFY.value
    YOUTUBE = "YouTube"


class PlaylistType(str, Enum):
    SPOTIFY = TrackSourceServiceName.SPOTIFY.value
    SOUNDCLOUD = TrackSourceServiceName.SOUNDCLOUD.value
    APPLE_MUSIC = TrackSourceServiceName.APPLE_MUSIC.value
    AGGREGATE = "Aggregate"


class TrackData(BaseModel):
    service_name: TrackSourceServiceName
    track_name: str | None = None
    artist_name: str | None = None
    track_url: str | None = None
    album_cover_url: str | None = None


class StartView(BaseModel):
    view_count: int | None = None
    timestamp: datetime | None = None


class CurrentView(BaseModel):
    view_count: int | None = None
    timestamp: datetime | None = None


class HistoricalView(BaseModel):
    total_view_count: int | None = None
    delta_view_count: int | None = None
    timestamp: datetime | None = None


class YouTubeView(BaseModel):
    view_count: int | None = None
    timestamp: datetime | None = None


class ServiceView(BaseModel):
    service_name: DataSourceServiceName
    start_view: StartView = Field(default_factory=StartView)
    current_view: CurrentView = Field(default_factory=CurrentView)
    historical_view: list[HistoricalView] = []
    youtube_view: YouTubeView = Field(default_factory=YouTubeView)


class ETLTrack(BaseModel):
    """ETL Track model - distinct from Django Track model."""

    isrc: str
    apple_music_track_data: TrackData = Field(
        default_factory=lambda: TrackData(service_name=TrackSourceServiceName.APPLE_MUSIC)
    )
    spotify_track_data: TrackData = Field(
        default_factory=lambda: TrackData(service_name=TrackSourceServiceName.SPOTIFY)
    )
    soundcloud_track_data: TrackData = Field(
        default_factory=lambda: TrackData(service_name=TrackSourceServiceName.SOUNDCLOUD)
    )
    youtube_url: str | None = None
    spotify_view: ServiceView = Field(default_factory=lambda: ServiceView(service_name=DataSourceServiceName.SPOTIFY))
    youtube_view: ServiceView = Field(default_factory=lambda: ServiceView(service_name=DataSourceServiceName.YOUTUBE))


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: dict[TrackSourceServiceName, int]
    raw_aggregate_rank: int | None = None
    aggregate_service_name: TrackSourceServiceName | None = None


class Playlist(BaseModel):
    service_name: PlaylistType
    genre_name: GenreName
    tracks: list[TrackRank]


class NormalizedTrack(BaseModel):
    """Normalized track data for Phase C - maps to Track model fields."""

    position: int
    isrc: str | None = None
    name: str
    artist: str
    album: str | None = None
    spotify_url: str | None = None
    apple_music_url: str | None = None
    soundcloud_url: str | None = None
    album_cover_url: str | None = None

    @property
    def service_url(self) -> str:
        """Get the service-specific URL for this track."""
        return self.spotify_url or self.apple_music_url or self.soundcloud_url or ""
