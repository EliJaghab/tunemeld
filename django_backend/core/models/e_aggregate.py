"""
Aggregate phase models for TuneMeld ETL pipeline.
"""

from typing import ClassVar

from core.models.a_lookup_tables import Genre, Service
from core.models.transform import Track
from django.db import models


class Playlist(models.Model):
    """
    Represents a curated playlist for a specific genre and service.

    Playlists are genre-specific collections from different services. There's also
    an 'Aggregate' playlist type that combines top tracks across all services.

    Example:
        spotify_pop = Playlist(
            service=spotify_service,
            genre=pop_genre,
            playlist_type="service"
        )
        # Contains top 100 pop tracks from Spotify

        aggregate_rap = Playlist(
            genre=rap_genre,
            playlist_type="aggregate"
        )
        # Contains top tracks across all services for rap
    """

    PLAYLIST_TYPE_CHOICES: ClassVar = [
        ("service", "Service-specific playlist"),
        ("aggregate", "Cross-service aggregate playlist"),
    ]

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Service (null for aggregate playlists)",
    )
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, help_text="Genre of this playlist")
    playlist_type = models.CharField(max_length=20, choices=PLAYLIST_TYPE_CHOICES, default="service")
    tracks = models.ManyToManyField(Track, through="TrackPlaylist", related_name="playlists")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "playlists"
        indexes: ClassVar = [
            models.Index(fields=["genre", "playlist_type"]),
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["updated_at"]),
        ]
        unique_together: ClassVar = [("service", "genre")]

    def __str__(self):
        if self.playlist_type == "aggregate":
            return f"Aggregate {self.genre.display_name} Playlist"
        return f"{self.service.display_name} {self.genre.display_name} Playlist"


class TrackPlaylist(models.Model):
    """
    Links tracks to playlists with position and scoring information.

    The through model for the Track-Playlist many-to-many relationship.
    Includes position in playlist and various scoring metrics.

    Example:
        track_playlist = TrackPlaylist(
            track=flowers_track,
            playlist=spotify_pop_playlist,
            position=1,
            score=95.5
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    position = models.IntegerField(help_text="Position in playlist (1-based)")
    score = models.FloatField(null=True, blank=True, help_text="Calculated score for ranking (higher = better)")
    view_count_contribution = models.BigIntegerField(
        null=True, blank=True, help_text="View count used in score calculation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "track_playlists"
        indexes: ClassVar = [
            models.Index(fields=["playlist", "position"]),
            models.Index(fields=["track"]),
            models.Index(fields=["score"]),
        ]
        unique_together: ClassVar = [("track", "playlist")]
        ordering: ClassVar = ["position"]

    def __str__(self):
        return f"#{self.position}: {self.track} in {self.playlist}"


class PlaylistMetadata(models.Model):
    """
    Metadata and statistics for playlists.

    Stores additional information about playlists like update history,
    statistics, and configuration.

    Example:
        metadata = PlaylistMetadata(
            playlist=spotify_pop_playlist,
            total_tracks=100,
            last_updated=timezone.now(),
            update_frequency_hours=24
        )
    """

    id = models.BigAutoField(primary_key=True)
    playlist = models.OneToOneField(Playlist, on_delete=models.CASCADE, related_name="metadata")
    total_tracks = models.IntegerField(default=0, help_text="Current number of tracks in playlist")
    last_updated = models.DateTimeField(help_text="When playlist was last updated")
    update_frequency_hours = models.IntegerField(
        default=24, help_text="How often this playlist should be updated (hours)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this playlist is actively maintained")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "playlist_metadata"
        indexes: ClassVar = [
            models.Index(fields=["last_updated"]),
        ]

    def __str__(self):
        return f"Metadata for {self.playlist}"
