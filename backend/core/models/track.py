from typing import ClassVar

from django.core.validators import RegexValidator
from django.db import models


class TrackModel(models.Model):
    """
    Represents a unique music track identified by ISRC.

    Contains all track metadata including service-specific information.

    Example:
        track = TrackModel(
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
    )
    track_name = models.CharField(max_length=500, help_text="Name of the track")
    artist_name = models.CharField(max_length=500, help_text="Primary artist name")
    album_name = models.CharField(max_length=500, null=True, blank=True, help_text="Album name")

    spotify_url = models.URLField(null=True, blank=True, help_text="Spotify track URL")
    apple_music_url = models.URLField(null=True, blank=True, help_text="Apple Music track URL")
    youtube_url = models.URLField(null=True, blank=True, help_text="YouTube track URL")
    soundcloud_url = models.URLField(null=True, blank=True, help_text="SoundCloud track URL")
    genius_url = models.URLField(null=True, blank=True, help_text="Genius lyrics page URL")

    genius_lyrics = models.TextField(null=True, blank=True, help_text="Full song lyrics from Genius")

    album_cover_url = models.URLField(null=True, blank=True, help_text="Album cover image URL")

    aggregate_rank = models.IntegerField(null=True, blank=True, help_text="Cross-service aggregate ranking")
    aggregate_score = models.FloatField(null=True, blank=True, help_text="Cross-service aggregate score")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tracks"
        constraints: ClassVar = [models.UniqueConstraint(fields=["isrc"], name="unique_track_isrc")]
        indexes: ClassVar = [
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["artist_name"]),
            models.Index(fields=["isrc"]),
        ]

    def __str__(self):
        return f"{self.track_name} by {self.artist_name} ({self.isrc})"


class TrackFeatureModel(models.Model):
    """
    Audio features for tracks (Spotify audio features).

    Decoupled from TrackModel to keep features separate and extensible.
    """

    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        db_index=True,
        unique=True,
    )

    danceability = models.FloatField(help_text="Spotify danceability (0-1)")
    energy = models.FloatField(help_text="Spotify energy (0-1)")
    valence = models.FloatField(help_text="Spotify valence (0-1)")
    acousticness = models.FloatField(help_text="Spotify acousticness (0-1)")
    instrumentalness = models.FloatField(help_text="Spotify instrumentalness (0-1)")
    speechiness = models.FloatField(help_text="Spotify speechiness (0-1)")
    liveness = models.FloatField(help_text="Spotify liveness (0-1)")
    tempo = models.FloatField(help_text="Spotify tempo (BPM)")
    loudness = models.FloatField(help_text="Spotify loudness (dB)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "track_features"
        constraints: ClassVar = [models.UniqueConstraint(fields=["isrc"], name="unique_track_feature_isrc")]
        indexes: ClassVar = [
            models.Index(fields=["isrc"]),
        ]

    def __str__(self):
        return f"Features for {self.isrc}"
