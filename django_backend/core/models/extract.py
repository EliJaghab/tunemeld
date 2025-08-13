"""
Extraction phase models for TuneMeld ETL pipeline.
"""

from typing import ClassVar

from django.db import models

from .base import Genre, Service


class RawPlaylistData(models.Model):
    """
    Raw playlist data storage for ETL pipeline.

    Stores unprocessed playlist data as received from external APIs.
    This data is then transformed into the normalized models.

    The data field contains the full JSON response from services like:
    - Spotify API playlist tracks
    - Apple Music playlist data
    - SoundCloud playlist tracks

    Example:
        raw_data = RawPlaylistData(
            genre=pop_genre,
            service=spotify_service,
            playlist_url="https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd",
            playlist_name="RapCaviar",
            data={
                "tracks": [
                    {
                        "track": {
                            "id": "3nMVLPPw0PAcPwC8WXXwAs",
                            "name": "Flowers",
                            "artists": [{"name": "Miley Cyrus"}],
                            "external_ids": {"isrc": "USSM12345678"}
                        }
                    }
                ],
                "snapshot_id": "MTY3ODkw"
            }
        )
    """

    id = models.BigAutoField(primary_key=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, help_text="Genre of this playlist data")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service this data came from")

    # Playlist metadata
    playlist_url = models.URLField(help_text="Original playlist URL")
    playlist_name = models.CharField(max_length=255, blank=True, help_text="Playlist display name")
    playlist_cover_url = models.URLField(blank=True, help_text="Playlist cover image URL")
    playlist_cover_description_text = models.TextField(blank=True, help_text="Cover image description")
    playlist_tagline = models.TextField(blank=True, help_text="Playlist tagline/description")
    playlist_featured_artist = models.CharField(max_length=255, blank=True, help_text="Featured artist if any")
    playlist_saves_count = models.IntegerField(null=True, blank=True, help_text="Number of saves/followers")
    playlist_track_count = models.IntegerField(null=True, blank=True, help_text="Number of tracks")
    playlist_creator = models.CharField(max_length=255, blank=True, help_text="Playlist creator name")

    # Raw data and processing status
    data = models.JSONField(help_text="Raw JSON data from service API")
    processed = models.BooleanField(default=False, help_text="Whether this data has been processed by ETL")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When this data was processed")

    class Meta:
        db_table = "raw_playlist_data"
        indexes: ClassVar = [
            models.Index(fields=["genre", "service"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["processed"]),
            models.Index(fields=["playlist_url"]),
        ]
        ordering: ClassVar = ["-created_at"]

    def __str__(self):
        status = "processed" if self.processed else "pending"
        return f"Raw {self.service.name} {self.genre.name} data ({status})"


class ETLRun(models.Model):
    """
    Tracks ETL pipeline runs and their status.

    Records when ETL processes are executed, what data they processed,
    and whether they completed successfully.

    Example:
        run = ETLRun(
            stage="extract",
            service=spotify_service,
            genre=pop_genre,
            status="completed"
        )
    """

    STAGE_CHOICES: ClassVar = [
        ("extract", "Extract"),
        ("transform", "Transform"),
        ("load", "Load"),
        ("aggregate", "Aggregate"),
        ("view_count", "View Count Update"),
    ]

    STATUS_CHOICES: ClassVar = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.BigAutoField(primary_key=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, help_text="ETL pipeline stage")
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, null=True, blank=True, help_text="Service being processed"
    )
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, null=True, blank=True, help_text="Genre being processed")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0, help_text="Number of records processed")
    error_message = models.TextField(blank=True, help_text="Error details if failed")

    class Meta:
        db_table = "etl_runs"
        indexes: ClassVar = [
            models.Index(fields=["stage", "status"]),
            models.Index(fields=["started_at"]),
            models.Index(fields=["service", "genre"]),
        ]
        ordering: ClassVar = ["-started_at"]

    def __str__(self):
        service_genre = ""
        if self.service and self.genre:
            service_genre = f" ({self.service.name}/{self.genre.name})"
        return f"ETL {self.stage} - {self.status}{service_genre}"
