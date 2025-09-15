from typing import Any, TypedDict


class PlaylistMetadata(TypedDict, total=False):
    service_name: str
    genre_name: str
    playlist_name: str
    playlist_url: str
    playlist_cover_url: str | None
    playlist_cover_description_text: str | None
    playlist_tagline: str | None
    playlist_featured_artist: str | None
    playlist_track_count: int | None
    playlist_saves_count: str | None
    playlist_creator: str | None
    playlist_stream_url: str | None


class PlaylistData(TypedDict):
    metadata: PlaylistMetadata
    tracks: Any
