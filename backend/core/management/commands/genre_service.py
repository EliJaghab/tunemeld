import uuid
from typing import Any

from core.constants import GENRE_CONFIGS, RANK_CONFIGS, SERVICE_CONFIGS
from core.models import Genre, Rank, Service
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize Genre, Service, and Rank lookup tables for ETL pipelines"

    def handle(self, *args: Any, etl_run_id: uuid.UUID, **options: Any) -> None:
        for genre_name, config in GENRE_CONFIGS.items():
            Genre.objects.get_or_create(
                name=genre_name,
                etl_run_id=etl_run_id,
                defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]},
            )

        for service_name, config in SERVICE_CONFIGS.items():
            Service.objects.get_or_create(
                name=service_name,
                etl_run_id=etl_run_id,
                defaults={"display_name": config["display_name"], "icon_url": config["icon_url"]},
            )

        for rank_name, config in RANK_CONFIGS.items():
            Rank.objects.get_or_create(
                name=rank_name,
                etl_run_id=etl_run_id,
                defaults={
                    "display_name": config["display_name"],
                    "sort_field": config["sort_field"],
                    "sort_order": config["sort_order"],
                    "data_field": config["data_field"],
                },
            )
