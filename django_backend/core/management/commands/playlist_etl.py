import os
from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--staging", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        if options.get("staging"):
            os.environ["STAGING_MODE"] = "true"

        call_command("a_init_lookup_tables")
        call_command("b_raw_extract")
        call_command("c_normalize_raw_playlists")
        call_command("d_hydrate_tracks")
