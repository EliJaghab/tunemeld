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


class TrackData(BaseModel):
    service_name: ServiceName
    track_name: str | None = None
    artist_name: str | None = None
    track_url: HttpUrl | None = None


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


class Track(BaseModel):
    isrc: str
    soundcloud_track_data: TrackData | None = None
    spotify_track_data: TrackData | None = None
    apple_music_track_data: TrackData | None = None
    album_cover_url: HttpUrl | None = None
    youtube_url: HttpUrl | None = None
    spotify_views: ServiceView | None = None
    youtube_views: ServiceView | None = None


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: list[ServiceName]


class Playlist(BaseModel):
    service_name: ServiceName
    genre_name: str
    tracks: list[TrackRank]
