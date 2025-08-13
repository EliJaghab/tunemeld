"""
Base models for TuneMeld - Genre and Service lookup tables.
"""

from typing import ClassVar

from django.core.validators import RegexValidator
from django.db import models


class Genre(models.Model):
    """
    Music genres supported by the system.

    Simple lookup table for genres. Can be pre-populated with:
    - dance (Dance/Electronic)
    - rap (Hip-Hop/Rap)
    - country (Country)
    - pop (Pop)

    Example:
        pop_genre = Genre(name="pop", display_name="Pop")
        pop_genre.save()
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=50,
        unique=True,
        validators=[RegexValidator(r"^[a-z_]+$", "Genre names must be lowercase with underscores")],
        help_text="Internal genre identifier (lowercase, underscores only)",
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable genre name")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "genres"
        ordering: ClassVar = ["name"]

    def __str__(self):
        return self.display_name


class Service(models.Model):
    """
    Music streaming services that provide playlist data.

    Represents different music platforms like Spotify, Apple Music, etc.
    Services can be track sources (provide tracks) and/or data sources
    (provide metadata like view counts).

    Example:
        spotify = Service(
            name="Spotify",
            display_name="Spotify",
            is_track_source=True,
            is_data_source=True
        )
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[RegexValidator(r"^[A-Za-z][A-Za-z0-9_]*$", "Service names must be alphanumeric")],
        help_text="Internal service identifier",
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable service name")
    is_track_source = models.BooleanField(default=True, help_text="Whether this service provides track listings")
    is_data_source = models.BooleanField(
        default=False, help_text="Whether this service provides metadata (view counts, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "services"
        ordering: ClassVar = ["name"]

    def __str__(self):
        capabilities = []
        if self.is_track_source:
            capabilities.append("tracks")
        if self.is_data_source:
            capabilities.append("data")
        cap_str = "+".join(capabilities) if capabilities else "none"
        return f"{self.display_name} ({cap_str})"
