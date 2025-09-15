import uuid
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from core.constants import GenreName, ServiceName
from core.models.b_genre_service import Genre, Service
from django.core.validators import RegexValidator
from django.db import models
from pydantic import BaseModel

if TYPE_CHECKING:
    from core.models.f_track import TrackRank


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

    etl_run_id = models.UUIDField(default=uuid.uuid4, help_text="ETL run identifier for blue-green deployments")

    class Meta:
        db_table = "playlists"
        ordering: ClassVar = ["service", "genre", "position"]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
            models.Index(fields=["etl_run_id"]),
        ]
        unique_together: ClassVar = [("service", "genre", "position", "etl_run_id")]

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
    etl_run_id = models.UUIDField(default=uuid.uuid4, help_text="ETL run identifier for blue-green deployments")

    class Meta:
        db_table = "service_tracks"
        unique_together: ClassVar = [("service", "genre", "position", "etl_run_id")]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["service", "isrc"]),
            models.Index(fields=["etl_run_id"]),
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
