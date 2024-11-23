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
    start_view_count: int
    start_timestamp: datetime


class CurrentView(BaseModel):
    current_view_count: int
    current_timestamp: datetime


class ServiceView(BaseModel):
    service_name: DataSourceServiceName
    start_view: StartView | None = None
    current_view: CurrentView | None = None
    views: int = 0


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
    spotify_views: ServiceView = Field(
        default_factory=lambda: ServiceView(service_name=DataSourceServiceName.SPOTIFY)
    )
    youtube_views: ServiceView = Field(
        default_factory=lambda: ServiceView(service_name=DataSourceServiceName.YOUTUBE)
    )


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: list[TrackSourceServiceName]


class Playlist(BaseModel):
    service_name: TrackSourceServiceName
    genre_name: str
    tracks: list[TrackRank]
