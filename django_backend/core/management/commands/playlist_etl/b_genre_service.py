"""
Initialize Genre and Service lookup tables.
Simple command for deployment - no output, just initialization.
"""

from core.models import Genre, Service
from django.core.management.base import BaseCommand

from django_backend.core.utils.constants import GENRE_DISPLAY_NAMES, SERVICE_CONFIGS


class Command(BaseCommand):
    help = "Initialize Genre and Service lookup tables"

    def handle(self, *args: object, **options: object) -> None:
        for genre_name, display_name in GENRE_DISPLAY_NAMES.items():
            Genre.objects.get_or_create(name=genre_name, defaults={"display_name": display_name})

        for service_name, config in SERVICE_CONFIGS.items():
            Service.objects.update_or_create(
                name=service_name,
                defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]},
            )
