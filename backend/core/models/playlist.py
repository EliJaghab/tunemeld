"""
Raw data models for Phase 2: RawPlaylistData storage.

This model stores unprocessed playlist data as received from external APIs.
The data is then normalized in Phase 3 and hydrated in Phase 4.
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict

from core.constants import GenreName, ServiceName
from core.models.genre_service import Genre, Service
from django.core.validators import RegexValidator
from django.db import models
from pydantic import BaseModel

if TYPE_CHECKING:
    from core.models.track import TrackRank


class RawPlaylistData(models.Model):
    """
    Raw playlist data storage for ETL pipeline.

    Stores unprocessed playlist data as received from external APIs.
    This data is then transformed into the normalized models.

    The data field contains the full JSON response from services like:
    - Spotify API playlist tracks
    - Apple Music playlist data
    - SoundCloud playlist tracks

    Created by: 02_raw_extract.py
    Used by: 03_normalize_raw_playlists.py
    """

    id = models.BigAutoField(primary_key=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, help_text="Genre of this playlist data")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service this data came from")

    playlist_url = models.URLField(help_text="Original playlist URL")
    playlist_name = models.CharField(max_length=255, blank=True, help_text="Playlist display name")
    playlist_cover_url = models.URLField(blank=True, help_text="Playlist cover image URL")
    playlist_cover_description_text = models.TextField(blank=True, help_text="Cover image description")

    data = models.JSONField(help_text="Raw JSON data from service API")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "raw_playlist_data"
        indexes: ClassVar = [
            models.Index(fields=["genre", "service"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["playlist_url"]),
        ]
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["service", "genre"], name="unique_raw_playlist_service_genre")
        ]
        ordering: ClassVar = ["-created_at"]

    def __str__(self) -> str:
        return f"Raw {self.service.name} {self.genre.name} data"


class Playlist(models.Model):
    """
    Playlist positioning data linking to ServiceTrack records.

    Stores the relationship between playlist positions and ServiceTrack records,
    with ISRC populated after Phase D resolution.

    Created by: c_normalize_raw_playlists.py
    Used by: Later phases for aggregation and ranking
    """

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    # ISRC (populated after Phase D resolution)
    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        db_index=True,
        null=True,
        blank=True,
    )

    # Link to the detailed service track record
    service_track = models.ForeignKey(
        "ServiceTrack",
        on_delete=models.CASCADE,
        help_text="Reference to the normalized service track record",
        related_name="playlists",
    )

    class Meta:
        db_table = "playlists"
        ordering: ClassVar = ["service", "genre", "position"]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
        ]
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["service", "genre", "position"], name="unique_playlist_position")
        ]

    def __str__(self) -> str:
        return f"Position {self.position}: {self.isrc} ({self.service.name} {self.genre.name})"


class ServiceTrack(models.Model):
    """Normalized track data from all services before consolidation."""

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(help_text="Position in playlist")

    # Track metadata
    track_name = models.CharField(max_length=500, help_text="Name of the track")
    artist_name = models.CharField(max_length=500, help_text="Primary artist name")
    album_name = models.CharField(max_length=500, null=True, blank=True, help_text="Album name")

    # Service-specific URL
    service_url = models.URLField(help_text="Service-specific track URL")

    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
    )

    album_cover_url = models.URLField(null=True, blank=True, help_text="Album cover image URL")

    track = models.ForeignKey(
        "Track",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Reference to consolidated Track record",
        related_name="service_tracks",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_tracks"
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["service", "genre", "position"], name="unique_service_track_position")
        ]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["service", "isrc"]),
        ]

    def __str__(self) -> str:
        return f"{self.track_name} by {self.artist_name} ({self.service.name})"


class PlaylistType(str, Enum):
    SPOTIFY = ServiceName.SPOTIFY.value
    SOUNDCLOUD = ServiceName.SOUNDCLOUD.value
    APPLE_MUSIC = ServiceName.APPLE_MUSIC.value
    TUNEMELD = ServiceName.TUNEMELD.value


class PlaylistETL(BaseModel):
    """Pydantic playlist model for aggregation and ranking."""

    service_name: PlaylistType
    genre_name: GenreName
    tracks: list["TrackRank"]


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


class Rank(models.Model):
    """
    Represents different ranking/sorting options for playlists.
    Backend-driven configuration for frontend sort buttons.
    """

    name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    sort_field = models.CharField(max_length=50)
    sort_order = models.CharField(max_length=4, choices=[("asc", "Ascending"), ("desc", "Descending")], default="asc")
    data_field = models.CharField(
        max_length=50,
        default="rank",
        help_text="Exact field name in track data (e.g., 'rank', 'spotifyCurrentViewCount')",
    )
    icon_class = models.CharField(max_length=50, help_text="CSS class for rank icon")

    class Meta:
        db_table = "ranks"
        constraints: ClassVar = [models.UniqueConstraint(fields=["name"], name="unique_rank_name")]
        indexes: ClassVar = [
            models.Index(fields=["name"]),
        ]
        ordering: ClassVar = ["id"]

    def __str__(self):
        return f"{self.display_name} ({self.name})"
