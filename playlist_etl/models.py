from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GenreName(str, Enum):
    DANCE = "dance"
    RAP = "rap"
    COUNTRY = "country"
    POP = "pop"


class TrackSourceServiceName(str, Enum):
    SPOTIFY = "Spotify"
    SOUNDCLOUD = "SoundCloud"
    APPLE_MUSIC = "AppleMusic"


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
    historical_view: list[HistoricalView] = list()
    youtube_view: YouTubeView = Field(default_factory=YouTubeView)


class Track(BaseModel):
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
    spotify_view: ServiceView = Field(
        default_factory=lambda: ServiceView(service_name=DataSourceServiceName.SPOTIFY)
    )
    youtube_view: ServiceView = Field(
        default_factory=lambda: ServiceView(service_name=DataSourceServiceName.YOUTUBE)
    )


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: dict[TrackSourceServiceName, int]
    raw_aggregate_rank: int | None = None
    aggregate_service_name: TrackSourceServiceName | None = None


class Playlist(BaseModel):
    service_name: PlaylistType
    genre_name: str
    tracks: list[TrackRank]
