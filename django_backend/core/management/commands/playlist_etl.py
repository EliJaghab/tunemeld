from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def add_arguments(self, parser):
        pass

    def handle(self, *args: Any, **options: Any) -> None:
        call_command("a_genre_service")
        call_command("b_raw_playlist")
        call_command("c_playlist_service_track")
        call_command("d_track")
        call_command("e_aggregate")
        call_command("f_clear_cache")
        call_command("g_warm_cache")
