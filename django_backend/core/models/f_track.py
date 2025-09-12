import uuid
from typing import ClassVar

from django.core.validators import RegexValidator
from django.db import models
from pydantic import BaseModel, Field

from playlist_etl.constants import ServiceName


class Track(models.Model):
    """
    Represents a unique music track identified by ISRC and ETL run.

    Contains all track metadata including service-specific information.
    Uses composite unique constraint on (isrc, etl_run_id) for blue-green deployments.
    Primary key is isrc field (not auto-incrementing id).

    Example:
        track = Track(
            isrc="USSM12201546",
            track_name="Flowers",
            artist_name="Miley Cyrus",
            album_name="Endless Summer Vacation",
            spotify_url="https://open.spotify.com/track/7xGfFoTpQ2E7fRF5lN10tr"
        )
    """

    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        primary_key=True,
    )
    track_name = models.CharField(max_length=500, help_text="Name of the track")
    artist_name = models.CharField(max_length=500, help_text="Primary artist name")
    album_name = models.CharField(max_length=500, null=True, blank=True, help_text="Album name")

    spotify_url = models.URLField(null=True, blank=True, help_text="Spotify track URL")
    apple_music_url = models.URLField(null=True, blank=True, help_text="Apple Music track URL")
    youtube_url = models.URLField(null=True, blank=True, help_text="YouTube track URL")
    soundcloud_url = models.URLField(null=True, blank=True, help_text="SoundCloud track URL")

    album_cover_url = models.URLField(null=True, blank=True, help_text="Album cover image URL")

    aggregate_rank = models.IntegerField(null=True, blank=True, help_text="Cross-service aggregate ranking")
    aggregate_score = models.FloatField(null=True, blank=True, help_text="Cross-service aggregate score")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    etl_run_id = models.UUIDField(default=uuid.uuid4, help_text="ETL run identifier for blue-green deployments")

    class Meta:
        db_table = "tracks"
        unique_together: ClassVar = [("isrc", "etl_run_id")]
        indexes: ClassVar = [
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["artist_name"]),
            models.Index(fields=["etl_run_id"]),
            models.Index(fields=["isrc"]),
        ]

    def __str__(self):
        return f"{self.track_name} by {self.artist_name} ({self.isrc})"


TrackSourceServiceName = ServiceName


class TrackData(BaseModel):
    service_name: TrackSourceServiceName
    track_name: str | None = None
    artist_name: str | None = None
    track_url: str | None = None
    album_cover_url: str | None = None


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


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: dict[TrackSourceServiceName, int]
    raw_aggregate_rank: int | None = None
    aggregate_service_name: TrackSourceServiceName | None = None


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
