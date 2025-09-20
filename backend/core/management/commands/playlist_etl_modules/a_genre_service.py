"""
Initialize Genre, Service, and Rank lookup tables.
Simple command for deployment - no output, just initialization.
"""

from core.constants import GENRE_CONFIGS, RANK_CONFIGS, SERVICE_CONFIGS
from core.models import Genre, Rank, Service
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize Genre, Service, and Rank lookup tables"

    def handle(self, *args: object, **options: object) -> None:
        for genre_name, config in GENRE_CONFIGS.items():
            Genre.objects.get_or_create(
                name=genre_name, defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]}
            )

        for service_name, config in SERVICE_CONFIGS.items():
            Service.objects.update_or_create(
                name=service_name,
                defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]},
            )

        for rank_name, config in RANK_CONFIGS.items():
            Rank.objects.update_or_create(
                name=rank_name,
                defaults={
                    "display_name": config["display_name"],
                    "sort_field": config["sort_field"],
                    "sort_order": config["sort_order"],
                    "data_field": config["data_field"],
                    "icon_url": config["icon_url"],
                },
            )
