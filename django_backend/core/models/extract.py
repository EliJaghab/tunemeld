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

    # Raw data
    data = models.JSONField(help_text="Raw JSON data from service API")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "raw_playlist_data"
        indexes: ClassVar = [
            models.Index(fields=["genre", "service"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["playlist_url"]),
        ]
        ordering: ClassVar = ["-created_at"]

    def __str__(self):
        return f"Raw {self.service.name} {self.genre.name} data"
