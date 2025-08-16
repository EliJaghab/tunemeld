import json
from pathlib import Path
from typing import Any

from core.models import Genre, RawPlaylistData, Service
from core.utils import initialize_lookup_tables
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load real API data from files"

    def handle(self, *args: Any, **options: Any) -> None:
        initialize_lookup_tables()
        real_api_data_dir = Path("real_api_data")

        if not real_api_data_dir.exists():
            return

        mapping = {"spotify": "Spotify", "apple_music": "AppleMusic", "soundcloud": "SoundCloud"}

        for service_dir in real_api_data_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name not in mapping:
                continue

            service = Service.objects.get(name=mapping[service_dir.name])

            for json_file in service_dir.glob("*.json"):
                genre = Genre.objects.get(name=json_file.stem)
                with open(json_file) as f:
                    data = json.load(f)

                RawPlaylistData.objects.create(
                    genre=genre,
                    service=service,
                    playlist_url=f"https://example.com/{service_dir.name}/{json_file.stem}",
                    playlist_name=f"{service.display_name} {genre.display_name} Playlist",
                    data=data,
                )
