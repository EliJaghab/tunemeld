"""
Core utility functions for TuneMeld Django backend.
"""

from core.models import Genre, Service

from playlist_etl.constants import GENRE_DISPLAY_NAMES, SERVICE_CONFIGS


def initialize_lookup_tables():
    for genre_name, display_name in GENRE_DISPLAY_NAMES.items():
        Genre.objects.get_or_create(name=genre_name, defaults={"display_name": display_name})

    for service_name in SERVICE_CONFIGS:
        Service.objects.get_or_create(
            name=service_name,
            defaults={"display_name": service_name},
        )
