from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl


class GenreName(str, Enum):
    DANCE = "dance"
    RAP = "rap"
    COUNTRY = "country"
    POP = "pop"


class ServiceName(str, Enum):
    AGGREGATE = "Aggregate"
    SPOTIFY = "Spotify"
    YOUTUBE = "YouTube"
    SOUNDCLOUD = "SoundCloud"
    APPLE_MUSIC = "AppleMusic"


class TrackServiceData(BaseModel):
    spotify_track_name: str | None = None
    spotify_artist_name: str | None = None
    spotify_track_url: HttpUrl | None = None
    soundcloud_track_name: str | None = None
    soundcloud_artist_name: str | None = None
    soundcloud_track_url: HttpUrl | None = None
    apple_music_track_name: str | None = None
    apple_music_artist_name: str | None = None
    apple_music_track_url: HttpUrl | None = None
    album_cover_url: HttpUrl | None = None
    youtube_url: HttpUrl | None = None


class StartView(BaseModel):
    start_view_count: int
    start_timestamp: datetime


class CurrentView(BaseModel):
    current_view_count: int
    current_timestamp: datetime


class ServiceView(BaseModel):
    service_name: ServiceName
    start_view: StartView
    current_view: CurrentView


class View(BaseModel):
    spotify_views: ServiceView
    youtube_views: ServiceView


class Track(BaseModel):
    isrc: str
    service_data: TrackServiceData
    view_count_data: View | None = None


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: list[str]


class PlaylistRank(BaseModel):
    service_name: ServiceName
    genre_name: str
    tracks: list[TrackRank]
