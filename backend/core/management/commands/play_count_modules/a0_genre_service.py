"""
Initialize Genre, Service, and Rank lookup tables with ETL run ID pattern.
Ensures all required reference data exists before running play count ETL.
"""

import uuid
from typing import Any

from core.constants import GENRE_CONFIGS, RANK_CONFIGS, SERVICE_CONFIGS
from core.models import Genre, Rank, Service
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize Genre, Service, and Rank lookup tables for Play Count ETL"

    def handle(self, *args: Any, etl_run_id: uuid.UUID | None = None, **options: Any) -> None:
        """
        Initialize all lookup tables required for play count ETL.
        Uses get_or_create/update_or_create pattern to ensure data exists without wiping.
        """
        etl_run_id or uuid.uuid4()

        # Initialize Genre lookup table
        for genre_name, config in GENRE_CONFIGS.items():
            Genre.objects.get_or_create(
                name=genre_name, defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]}
            )

        # Initialize Service lookup table
        for service_name, config in SERVICE_CONFIGS.items():
            Service.objects.update_or_create(
                name=service_name,
                defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]},
            )

        # Initialize Rank lookup table
        for rank_name, config in RANK_CONFIGS.items():
            Rank.objects.update_or_create(
                name=rank_name,
                defaults={
                    "display_name": config["display_name"],
                    "sort_field": config["sort_field"],
                    "sort_order": config["sort_order"],
                    "data_field": config["data_field"],
                },
            )
