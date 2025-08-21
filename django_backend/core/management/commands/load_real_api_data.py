import json
from pathlib import Path
from typing import Any

from core.models import Genre, RawPlaylistData, Service
from core.utils import initialize_lookup_tables
from django.core.management.base import BaseCommand

from playlist_etl.constants import SERVICE_CONFIGS, ServiceName

MAX_TRACKS_PER_PLAYLIST = 5


class Command(BaseCommand):
    help = "Load real API data from files for staging environment"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        if options.get("clear"):
            RawPlaylistData.objects.all().delete()
        initialize_lookup_tables()
        real_api_data_dir = Path(__file__).parent.parent.parent.parent / "real_api_data"

        if not real_api_data_dir.exists():
            return

        mapping = {
            "spotify": ServiceName.SPOTIFY,
            "apple_music": ServiceName.APPLE_MUSIC,
            "soundcloud": ServiceName.SOUNDCLOUD,
        }

        for service_dir in real_api_data_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name not in mapping:
                continue

            service = Service.objects.get(name=mapping[service_dir.name])

            for json_file in service_dir.glob("*.json"):
                genre = Genre.objects.get(name=json_file.stem)
                with open(json_file) as f:
                    data = json.load(f)

                limited_data = self.limit_tracks_in_playlist(service_dir.name, data)

                playlist_metadata = self.extract_playlist_metadata(service_dir.name, json_file.stem, limited_data)

                RawPlaylistData.objects.create(
                    genre=genre,
                    service=service,
                    playlist_url=playlist_metadata["url"],
                    playlist_name=playlist_metadata["name"],
                    playlist_cover_url=playlist_metadata["cover_url"],
                    playlist_cover_description_text=playlist_metadata["description"],
                    data=limited_data,
                )

    def extract_playlist_metadata(self, service: str, genre: str, data: dict) -> dict[str, str]:
        """Extract playlist metadata from JSON data with realistic stub data for missing fields."""
        service_mapping = {
            "spotify": ServiceName.SPOTIFY,
            "apple_music": ServiceName.APPLE_MUSIC,
            "soundcloud": ServiceName.SOUNDCLOUD,
        }
        service_name = service_mapping[service]
        config = SERVICE_CONFIGS[service_name]
        playlist_url = config["links"][genre]

        metadata = {"url": playlist_url, "name": "", "cover_url": "", "description": ""}

        # this is webscraped data that does not come in the json payload
        if service == "soundcloud":
            metadata["url"] = data.get("permalinkUrl", playlist_url)
            track_count = len(data.get("tracks", []))
            if genre == "dance":
                metadata["name"] = "New EDM Hits: On The Up"
                metadata["description"] = (
                    f"The freshest electronic dance music trending now. {track_count} tracks updated weekly "
                    "to keep you moving."
                )
            elif genre == "rap":
                metadata["name"] = "Hip-Hop Central 2024"
                metadata["description"] = (
                    f"The hottest rap tracks and hip-hop bangers. {track_count} songs featuring today's "
                    "biggest artists."
                )
            elif genre == "pop":
                metadata["name"] = "Pop Hits 2024 ⚡️ Top 100 Trending"
                metadata["description"] = (
                    f"The biggest pop hits dominating the charts. {track_count} tracks updated weekly."
                )
            elif genre == "country":
                metadata["name"] = "Country Gold"
                metadata["description"] = (
                    f"The best of country music from Nashville and beyond. {track_count} tracks curated "
                    "for country fans."
                )
            metadata["cover_url"] = f"https://i1.sndcdn.com/artworks-{genre}-playlist-large.jpg"

        elif service == "spotify":
            total_tracks = data.get("total", 0)
            if genre == "dance":
                metadata["name"] = "Electronic Hits"
                metadata["description"] = (
                    f"Pulsing beats and electronic anthems. {total_tracks} tracks to energize your day."
                )
            elif genre == "rap":
                metadata["name"] = "RapCaviar"
                metadata["description"] = (
                    f"New music from hip-hop's biggest names and rising stars. {total_tracks} tracks."
                )
            elif genre == "pop":
                metadata["name"] = "Today's Top Hits"
                metadata["description"] = (
                    f"The most played songs right now. {total_tracks} tracks featuring today's biggest hits."
                )
            elif genre == "country":
                metadata["name"] = "Hot Country"
                metadata["description"] = (
                    f"The biggest songs in country music. {total_tracks} tracks from country's finest."
                )
            metadata["cover_url"] = f"https://i.scdn.co/image/ab67706f00000002{genre[:8].zfill(8)}"

        elif service == "apple_music":
            track_count = len(data.get("album_details", {}))
            if genre == "dance":
                metadata["name"] = "danceXL Apple Music Dance"
                metadata["description"] = (
                    f"On danceXL, we highlight the biggest club tracks primed for mainstream crossover. "
                    f"{track_count} tracks from the global dance scene."
                )
                metadata["cover_url"] = (
                    "https://mvod.itunes.apple.com/itunes-assets/HLSMusic115/v4/7a/c6/ca/7ac6ca6d-4a09-98a4-3f00-b828b72c9c9e/P359085557_default.m3u8"
                )
            elif genre == "rap":
                metadata["name"] = "Rap Life Apple Music Hip-Hop"
                metadata["description"] = (
                    f"Rap Life is home to hip-hop's heavy hitters and its vanguard—the songs that speak "
                    f"to the moment. {track_count} tracks."
                )
                metadata["cover_url"] = (
                    "https://mvod.itunes.apple.com/itunes-assets/HLSMusic122/v4/63/5f/47/635f47b8-d679-2d25-fae8-2dd0104ae786/P470409701_default.m3u8"
                )
            elif genre == "pop":
                metadata["name"] = "A-List Pop Apple Music Pop"
                metadata["description"] = (
                    f"The songs that define pop culture today. {track_count} tracks from pop's biggest "
                    "stars and rising artists."
                )
                metadata["cover_url"] = (
                    "https://mvod.itunes.apple.com/itunes-assets/HLSMusic120/v4/8b/3e/42/8b3e42d8-9c8f-2c45-d5bc-f1e7392cd8bb/P359220499_default.m3u8"
                )
            elif genre == "country":
                metadata["name"] = "Today's Country Apple Music Country"
                metadata["description"] = (
                    f"This playlist tracks what's happening from the heart of the country scene to its "
                    f"outer edges. {track_count} tracks."
                )
                metadata["cover_url"] = (
                    "https://mvod.itunes.apple.com/itunes-assets/HLSMusic116/v4/cf/e3/25/cfe325dd-28c2-6396-d44d-12dae4f55ccb/P359220500_default.m3u8"
                )

        return metadata

    def limit_tracks_in_playlist(self, service: str, data: dict) -> dict:
        """Limit tracks in playlist to first MAX_TRACKS_PER_PLAYLIST positions."""
        limited_data = data.copy()

        if service == "spotify":
            # Spotify format: {"items": [{"track": {...}}, ...]}
            if "items" in limited_data:
                limited_data["items"] = limited_data["items"][:MAX_TRACKS_PER_PLAYLIST]
                limited_data["total"] = len(limited_data["items"])

        elif service == "soundcloud":
            # SoundCloud format: {"tracks": {"items": [...]}}
            if "tracks" in limited_data and "items" in limited_data["tracks"]:
                limited_data["tracks"]["items"] = limited_data["tracks"]["items"][:MAX_TRACKS_PER_PLAYLIST]

        elif service == "apple_music" and "album_details" in limited_data:
            # Apple Music format: {"album_details": {"0": {...}, "1": {...}, ...}}
            # Keep only first N numbered keys (0, 1, 2, 3, 4 for MAX_TRACKS_PER_PLAYLIST=5)
            album_details = limited_data["album_details"]
            limited_album_details = {}
            for i in range(min(MAX_TRACKS_PER_PLAYLIST, len(album_details))):
                if str(i) in album_details:
                    limited_album_details[str(i)] = album_details[str(i)]
            limited_data["album_details"] = limited_album_details

        return limited_data
