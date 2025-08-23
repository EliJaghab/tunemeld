import json
from pathlib import Path
from typing import Any

from core.models import Genre, RawPlaylistData, Service
from core.utils import initialize_lookup_tables
from django.core.management.base import BaseCommand

from playlist_etl.constants import SERVICE_CONFIGS, ServiceName

MAX_TRACKS_PER_PLAYLIST = 10


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

        # Real production metadata from MongoDB
        if service == "soundcloud":
            metadata["url"] = data.get("permalinkUrl", playlist_url)
            track_count = len(data.get("tracks", []))
            if genre == "dance":
                metadata["name"] = "New EDM Hits: On The Up"
                metadata["description"] = (
                    "Listen to New EDM Hits: On The Up, a playlist curated by SoundCloud on desktop and mobile."
                )
                metadata["cover_url"] = "https://i1.sndcdn.com/artworks-ZktqANNPL6Iv-0-t500x500.jpg"
            elif genre == "rap":
                metadata["name"] = "Hip-Hop Central 2024"
                metadata["description"] = (
                    "Listen to Hip-Hop Central, a playlist curated by SoundCloud on desktop and mobile."
                )
                metadata["cover_url"] = "https://i1.sndcdn.com/artworks-BzofT6IH3SbJ-0-t500x500.jpg"
            elif genre == "pop":
                metadata["name"] = "Pop Hits 2024 ⚡️ Top 100 Trending & Clean Pop Music"
                metadata["description"] = (
                    "Listen to Pop Hits 2024 ⚡️ Top 100 Trending & Clean Pop Music, "
                    "a playlist curated by NightSoul on desktop and mobile."
                )
                metadata["cover_url"] = "https://i1.sndcdn.com/artworks-ascSlTh2XuCP-0-t500x500.jpg"
            elif genre == "country":
                metadata["name"] = "Country Gold"
                metadata["description"] = (
                    "Listen to Country Gold, a playlist curated by SoundCloud on desktop and mobile."
                )
                metadata["cover_url"] = "https://i1.sndcdn.com/artworks-qAFQzGJwGCcQ-0-t500x500.jpg"

        elif service == "spotify":
            data.get("total", 0)
            if genre == "dance":
                metadata["name"] = "Electronic Hits"
                metadata["description"] = "Pulsing beats and electronic anthems to energize your day."
                metadata["cover_url"] = "https://i.scdn.co/image/ab67706f00000002de32e22b3b9a42c05e61cf1e"
            elif genre == "rap":
                metadata["name"] = "RapCaviar"
                metadata["description"] = "New music from hip-hop's biggest names and rising stars."
                metadata["cover_url"] = "https://i.scdn.co/image/ab67706f00000002dc222dc7e8ca2af6b3ba0eda"
            elif genre == "pop":
                metadata["name"] = "Today's Top Hits"
                metadata["description"] = "The hottest 50. Cover: Ravyn Lenae"
                metadata["cover_url"] = "https://i.scdn.co/image/ab67706f00000002a8be38445ab85cd96201e0f2"
            elif genre == "country":
                metadata["name"] = "Hot Country"
                metadata["description"] = "The biggest songs in country music from country's finest."
                metadata["cover_url"] = "https://i.scdn.co/image/ab67706f000000028e9cf01b5e2d83dfabece6c6"

        elif service == "apple_music":
            track_count = len(data.get("album_details", {}))
            if genre == "dance":
                metadata["name"] = "danceXL Apple Music Dance"
                metadata["description"] = (
                    f"On danceXL, we highlight the biggest club tracks primed for mainstream crossover. "
                    f"{track_count} tracks from the global dance scene."
                )
                metadata["cover_url"] = (
                    "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/59/63/5e/59635e3b-7dce-3436-a0eb-8ecc564c426a/mza_17421468509622388447.png/296x296bb.jpg"
                )
            elif genre == "rap":
                metadata["name"] = "Rap Life Apple Music Hip-Hop"
                metadata["description"] = (
                    f"Rap Life is home to hip-hop's heavy hitters and its vanguard—the songs that speak "
                    f"to the moment. {track_count} tracks."
                )
                metadata["cover_url"] = (
                    "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/ad/71/dd/ad71dd2b-0673-c915-47b8-e46df99e8e5e/mza_5738536155853078823.png/296x296bb.jpg"
                )
            elif genre == "pop":
                metadata["name"] = "A-List Pop Apple Music Pop"
                metadata["description"] = (
                    f"The songs that define pop culture today. {track_count} tracks from pop's biggest "
                    "stars and rising artists."
                )
                metadata["cover_url"] = (
                    "https://is1-ssl.mzstatic.com/image/thumb/Music122/v4/04/a8/40/04a840d2-da7f-7894-4741-3e6ccd9b09b8/mza_8054457354980901388.png/296x296bb.jpg"
                )
            elif genre == "country":
                metadata["name"] = "Today's Country Apple Music Country"
                metadata["description"] = (
                    f"This playlist tracks what's happening from the heart of the country scene to its "
                    f"outer edges. {track_count} tracks."
                )
                metadata["cover_url"] = (
                    "https://is1-ssl.mzstatic.com/image/thumb/Music122/v4/e1/7a/96/e17a96dc-f063-10a0-5d0e-bb8dd8a02c7f/mza_14127025726718981556.png/296x296bb.jpg"
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
