"""
Lookup table models for Phase 1: Genre and Service tables.

These are the foundation tables that must be initialized before
any other ETL operations can begin.
"""

import uuid
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
        validators=[RegexValidator(r"^[a-z_]+$", "Genre names must be lowercase with underscores")],
        help_text="Internal genre identifier (lowercase, underscores only)",
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable genre name")
    icon_class = models.CharField(max_length=50, help_text="CSS class for genre icon")
    icon_url = models.CharField(max_length=200)
    etl_run_id = models.UUIDField(default=uuid.uuid4, help_text="ETL run identifier for blue-green deployments")

    class Meta:
        db_table = "genres"
        unique_together: ClassVar = [("name", "etl_run_id")]
        indexes: ClassVar = [
            models.Index(fields=["name"]),
            models.Index(fields=["etl_run_id"]),
        ]
        ordering: ClassVar = ["name"]

    def __str__(self) -> str:
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
            display_name="Spotify"
        )
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        validators=[RegexValidator(r"^[A-Za-z][A-Za-z0-9_]*$", "Service names must be alphanumeric")],
        help_text="Internal service identifier",
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable service name")
    icon_url = models.CharField(max_length=200, help_text="URL to service icon image", default="")
    etl_run_id = models.UUIDField(default=uuid.uuid4, help_text="ETL run identifier for blue-green deployments")

    class Meta:
        db_table = "services"
        unique_together: ClassVar = [("name", "etl_run_id")]
        indexes: ClassVar = [
            models.Index(fields=["name"]),
            models.Index(fields=["etl_run_id"]),
        ]
        ordering: ClassVar = ["name"]

    def __str__(self) -> str:
        return self.display_name
