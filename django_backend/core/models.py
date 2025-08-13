"""
Django models for TuneMeld - PostgreSQL migration from MongoDB
This module defines all database models for the playlist aggregation system.
"""

from typing import ClassVar

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class Genre(models.Model):
    """
    Music genres supported by the system.

    Simple lookup table for genres. Can be pre-populated with:
    - dance (Dance/Electronic)
    - rap (Hip-Hop/Rap)
    - country (Country)
    - pop (Pop)

    Example:
        Genre.objects.create(
            name="pop",
            display_name="Pop"
        )
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=50, unique=True, help_text="Internal genre identifier (e.g., 'dance', 'rap', 'country', 'pop')"
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable genre name for UI")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "genres"
        ordering: ClassVar = ["name"]

    def __str__(self):
        return self.display_name


class Service(models.Model):
    """
    Music streaming services that provide data.

    Simple lookup table for services. Can be pre-populated with:
    - Spotify (track source)
    - SoundCloud (track source)
    - AppleMusic (track source)
    - YouTube (data source for view counts)

    Example:
        Service.objects.create(
            name="Spotify",
            display_name="Spotify",
            is_track_source=True,
            is_data_source=True  # Spotify provides both tracks and view data
        )
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Service identifier (e.g., 'Spotify', 'AppleMusic', 'SoundCloud', 'YouTube')",
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable service name for UI")
    is_track_source = models.BooleanField(default=False, help_text="True if this service provides track/playlist data")
    is_data_source = models.BooleanField(default=False, help_text="True if this service provides view count data")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "services"
        ordering: ClassVar = ["name"]

    def __str__(self):
        return self.display_name


class Track(models.Model):
    """
    Represents a unique music track identified by ISRC code.

    The International Standard Recording Code (ISRC) is the primary identifier for tracks.
    This ensures the same song across different services is recognized as one entity.
    Stores core track information that's service-agnostic.

    Example:
        track = Track(
            isrc="USSM12345678",
            youtube_url="https://youtube.com/watch?v=abc123"
        )
        # ISRC USSM12345678 might be "Flowers" by Miley Cyrus
        # Same ISRC used across Spotify, Apple Music, etc.
    """

    isrc = models.CharField(
        max_length=12,
        primary_key=True,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (e.g., 'USSM12345678')",
    )
    youtube_url = models.URLField(blank=True, null=True, help_text="YouTube video URL for this track")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    primary_artist = models.CharField(
        max_length=255, blank=True, help_text="Primary artist name (aggregated from services)"
    )
    primary_title = models.CharField(
        max_length=255, blank=True, help_text="Primary track title (aggregated from services)"
    )

    class Meta:
        db_table = "tracks"
        indexes: ClassVar = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"{self.primary_title} - {self.primary_artist}" if self.primary_title else self.isrc


class TrackData(models.Model):
    """
    Service-specific metadata for a track.

    Each track can have different metadata on different services (slightly different titles,
    artist names, album covers, etc.). This model stores that service-specific information.

    Example:
        spotify_data = TrackData(
            track_id="USSM12345678",
            service_id=1,  # Spotify
            track_name="Flowers",
            artist_name="Miley Cyrus",
            track_url="https://open.spotify.com/track/...",
            album_cover_url="https://i.scdn.co/image/..."
        )

        apple_data = TrackData(
            track_id="USSM12345678",  # Same ISRC
            service_id=2,  # Apple Music
            track_name="Flowers (Radio Edit)",  # Slightly different title
            artist_name="Miley Cyrus",
            track_url="https://music.apple.com/...",
            album_cover_url="https://is1-ssl.mzstatic.com/..."
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(
        Track, on_delete=models.CASCADE, related_name="track_data", help_text="The track this data belongs to"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="The service this data comes from")
    track_name = models.CharField(
        max_length=255, blank=True, null=True, help_text="Track title as shown on this service"
    )
    artist_name = models.CharField(
        max_length=255, blank=True, null=True, help_text="Artist name as shown on this service"
    )
    track_url = models.URLField(blank=True, null=True, help_text="Direct URL to track on this service")
    album_cover_url = models.URLField(blank=True, null=True, help_text="Album artwork URL from this service")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "track_data"
        unique_together = ("track", "service")
        indexes: ClassVar = [
            models.Index(fields=["track", "service"]),
            models.Index(fields=["artist_name"]),
            models.Index(fields=["track_name"]),
        ]

    def __str__(self):
        return f"{self.track_name} by {self.artist_name} on {self.service.name}"


class Playlist(models.Model):
    """
    Represents a curated playlist for a specific genre and service.

    Playlists are genre-specific collections from different services. There's also
    an 'Aggregate' playlist type that combines top tracks across all services.

    Example:
        spotify_pop = Playlist(
            service_id=1,  # Spotify
            genre_id=4,    # Pop
            playlist_type="service"
        )
        # Contains top 100 pop tracks from Spotify

        aggregate_rap = Playlist(
            service=None,  # No specific service
            genre_id=2,    # Rap
            playlist_type="aggregate"
        )
        # Contains aggregated top rap tracks from all services
    """

    PLAYLIST_TYPE_CHOICES: ClassVar = [
        ("service", "Service Playlist"),  # From specific service
        ("aggregate", "Aggregate Playlist"),  # Combined from all services
    ]

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Service this playlist comes from (null for aggregate)",
    )
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, help_text="Music genre of this playlist")
    playlist_type = models.CharField(
        max_length=10,
        choices=PLAYLIST_TYPE_CHOICES,
        default="service",
        help_text="Type of playlist - service-specific or aggregate",
    )
    name = models.CharField(max_length=255, blank=True, help_text="Playlist name for display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "playlists"
        unique_together = ("service", "genre", "playlist_type")
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["playlist_type"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        if self.playlist_type == "aggregate":
            return f"Aggregate {self.genre.name} Playlist"
        return f"{self.service.name} {self.genre.name} Playlist"


class TrackPlaylist(models.Model):
    """
    Many-to-many relationship between tracks and playlists with ranking.

    This model represents a track's position in a playlist and stores ranking metadata.
    For aggregate playlists, it also stores how the track ranked on individual services.

    Example:
        # Track ranked #1 on Spotify Pop playlist
        track_playlist = TrackPlaylist(
            track_id="USSM12345678",
            playlist_id=1,  # Spotify Pop playlist
            rank=1,
            sources={}  # Not needed for service playlists
        )

        # Same track ranked #3 on Aggregate Pop playlist
        aggregate_entry = TrackPlaylist(
            track_id="USSM12345678",
            playlist_id=5,  # Aggregate Pop playlist
            rank=3,
            raw_aggregate_rank=2.5,  # Average across services
            sources={
                "Spotify": 1,
                "AppleMusic": 5,
                "SoundCloud": 2
            }
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, help_text="The track in this playlist")
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, help_text="The playlist containing this track")
    rank = models.IntegerField(help_text="Position in playlist (1 = top track)")
    raw_aggregate_rank = models.FloatField(
        blank=True, null=True, help_text="Weighted average rank for aggregate playlists"
    )
    sources = models.JSONField(
        default=dict,
        blank=True,
        help_text="Service rankings for aggregate playlists (e.g., {'Spotify': 1, 'AppleMusic': 5})",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "track_playlists"
        unique_together = ("track", "playlist")
        indexes: ClassVar = [
            models.Index(fields=["playlist", "rank"]),
            models.Index(fields=["track", "playlist"]),
            models.Index(fields=["added_at"]),
        ]
        ordering: ClassVar = ["rank"]

    def __str__(self):
        return f"#{self.rank} - {self.track} in {self.playlist}"


class ViewCount(models.Model):
    """
    Current view count data for a track on a specific service.

    Stores the most recent view count for tracking current popularity.
    Updated regularly by the ETL pipeline.

    Example:
        spotify_views = ViewCount(
            track_id="USSM12345678",
            service_id=1,  # Spotify
            view_count=15000000,
            timestamp=timezone.now()
        )

        youtube_views = ViewCount(
            track_id="USSM12345678",
            service_id=4,  # YouTube
            view_count=250000000,  # YouTube typically has higher counts
            timestamp=timezone.now()
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(
        Track, on_delete=models.CASCADE, related_name="view_counts", help_text="Track these views belong to"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service where views were counted")
    view_count = models.BigIntegerField(null=True, blank=True, help_text="Total view/play count")
    timestamp = models.DateTimeField(default=timezone.now, help_text="When this count was recorded")

    class Meta:
        db_table = "view_counts"
        indexes: ClassVar = [
            models.Index(fields=["track", "service", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
        ordering: ClassVar = ["-timestamp"]

    def __str__(self):
        return f"{self.track} - {self.view_count:,} views on {self.service}"


class HistoricalViewCount(models.Model):
    """
    Time-series historical view count data for trend analysis.

    Stores historical snapshots of view counts to track growth over time.
    Used for generating trend charts and calculating view velocity.

    Example:
        # Day 1 snapshot
        hist1 = HistoricalViewCount(
            track_id="USSM12345678",
            service_id=1,  # Spotify
            total_view_count=10000000,
            delta_view_count=500000,  # Gained 500k since last snapshot
            timestamp="2024-01-01"
        )

        # Day 2 snapshot
        hist2 = HistoricalViewCount(
            track_id="USSM12345678",
            service_id=1,
            total_view_count=10750000,
            delta_view_count=750000,  # Gained 750k (trending up!)
            timestamp="2024-01-02"
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name="historical_views",
        help_text="Track these historical views belong to",
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service where views were counted")
    total_view_count = models.BigIntegerField(
        null=True, blank=True, help_text="Total cumulative views at this point in time"
    )
    delta_view_count = models.BigIntegerField(null=True, blank=True, help_text="Change in views since last measurement")
    timestamp = models.DateTimeField(help_text="When this snapshot was taken")

    class Meta:
        db_table = "historical_view_counts"
        indexes: ClassVar = [
            models.Index(fields=["track", "service", "timestamp"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["track", "timestamp"]),
        ]
        ordering: ClassVar = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.track} - {self.total_view_count:,} total "
            f"(+{self.delta_view_count:,}) on {self.service} at {self.timestamp}"
        )


# ETL Support Models
class RawPlaylistData(models.Model):
    """
    Raw playlist data storage for ETL pipeline.

    Stores unprocessed playlist data as received from external APIs.
    This data is then transformed into the normalized models above.

    Example:
        raw_data = RawPlaylistData(
            genre_id=1,  # Pop
            service_id=1,  # Spotify
            data={
                "tracks": [
                    {
                        "position": 1,
                        "track": {
                            "id": "3nMVLPPw0PAcPwC8WXXwAs",
                            "name": "Flowers",
                            "artists": [{"name": "Miley Cyrus"}],
                            "external_ids": {"isrc": "USSM12345678"}
                        }
                    }
                ],
                "snapshot_id": "MTY3ODkw",
                "fetched_at": "2024-01-15T10:30:00Z"
            }
        )
    """

    id = models.BigAutoField(primary_key=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, help_text="Genre of this playlist data")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service this data came from")
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
        ]
        ordering: ClassVar = ["-created_at"]

    def __str__(self):
        status = "processed" if self.processed else "pending"
        return f"Raw {self.service.name} {self.genre.name} data ({status})"


class ETLRun(models.Model):
    """
    Tracks ETL pipeline execution history.

    Logs each run of the ETL pipeline for monitoring and debugging.

    Example:
        etl_run = ETLRun(
            run_type="full",
            status="success",
            started_at="2024-01-15T10:00:00Z",
            completed_at="2024-01-15T10:45:00Z",
            records_processed=5000,
            errors=0,
            metadata={
                "genres_processed": ["pop", "rap", "country", "dance"],
                "services_processed": ["Spotify", "AppleMusic", "SoundCloud"],
                "duration_seconds": 2700
            }
        )
    """

    RUN_TYPE_CHOICES: ClassVar = [
        ("full", "Full ETL"),
        ("incremental", "Incremental Update"),
        ("view_count", "View Count Update"),
        ("historical", "Historical Data Update"),
    ]

    STATUS_CHOICES: ClassVar = [
        ("running", "Running"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("partial", "Partial Success"),
    ]

    id = models.BigAutoField(primary_key=True)
    run_type = models.CharField(max_length=20, choices=RUN_TYPE_CHOICES, help_text="Type of ETL run")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="running", help_text="Current status of the run"
    )
    started_at = models.DateTimeField(auto_now_add=True, help_text="When the ETL run started")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When the ETL run completed")
    records_processed = models.IntegerField(default=0, help_text="Number of records processed")
    errors = models.IntegerField(default=0, help_text="Number of errors encountered")
    error_details = models.TextField(blank=True, help_text="Details of any errors encountered")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the run")

    class Meta:
        db_table = "etl_runs"
        indexes: ClassVar = [
            models.Index(fields=["status", "started_at"]),
            models.Index(fields=["run_type"]),
            models.Index(fields=["started_at"]),
        ]
        ordering: ClassVar = ["-started_at"]

    def __str__(self):
        return f"{self.run_type} - {self.status} at {self.started_at}"


class PlaylistMetadata(models.Model):
    """
    Stores metadata about playlists for tracking and analytics.

    Contains information about playlist updates, snapshot IDs, and other
    service-specific metadata.

    Example:
        metadata = PlaylistMetadata(
            playlist_id=1,  # Spotify Pop playlist
            last_snapshot_id="MTY3ODkw",
            total_tracks=100,
            last_updated="2024-01-15T10:00:00Z",
            metadata={
                "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
                "followers": 32500000,
                "description": "The hottest pop tracks",
                "collaborative": False
            }
        )
    """

    id = models.BigAutoField(primary_key=True)
    playlist = models.OneToOneField(
        Playlist, on_delete=models.CASCADE, related_name="metadata", help_text="The playlist this metadata belongs to"
    )
    last_snapshot_id = models.CharField(
        max_length=255, blank=True, help_text="Service-specific snapshot/version identifier"
    )
    total_tracks = models.IntegerField(default=0, help_text="Total number of tracks in playlist")
    last_updated = models.DateTimeField(help_text="When playlist was last fetched from service")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional service-specific metadata")

    class Meta:
        db_table = "playlist_metadata"
        indexes: ClassVar = [
            models.Index(fields=["last_updated"]),
        ]

    def __str__(self):
        return f"Metadata for {self.playlist}"
