"""Management command for RapidAPI cache operations"""

from typing import Any

from django.core.cache import cache
from django.core.management.base import BaseCommand

from playlist_etl.cache_utils import CACHE_TTL, get_cache_key
from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS


class Command(BaseCommand):
    help = "Manage RapidAPI cache - view stats, clear cache, etc."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all RapidAPI cache entries",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show cache statistics",
        )
        parser.add_argument(
            "--service",
            type=str,
            help="Service name to clear cache for (requires --genre)",
        )
        parser.add_argument(
            "--genre",
            type=str,
            help="Genre to clear cache for (requires --service)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["clear"]:
            self.clear_cache(options.get("service"), options.get("genre"))
        elif options["stats"]:
            self.show_stats()
        else:
            self.stdout.write("Use --help to see available options")

    def clear_cache(self, service: str | None = None, genre: str | None = None) -> None:
        """Clear cache entries"""
        if service and genre:
            # Clear specific service/genre combination
            # We need to reconstruct the URL to get the cache key
            if service in SERVICE_CONFIGS:
                config = SERVICE_CONFIGS[service]
                if service == "AppleMusic":
                    playlist_id = config["links"][genre].split("/")[-1]
                    apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
                    url = f"{config['base_url']}?url={apple_playlist_url}"
                elif service == "SoundCloud":
                    playlist_url = config["links"][genre]
                    url = f"{config['base_url']}?playlist={playlist_url}"
                else:
                    self.stdout.write(f"Service {service} doesn't use RapidAPI caching")
                    return

                cache_key = get_cache_key(service, genre, url)
                if cache.delete(cache_key):
                    self.stdout.write(self.style.SUCCESS(f"Cleared cache for {service}/{genre}"))
                else:
                    self.stdout.write(self.style.WARNING(f"No cache entry found for {service}/{genre}"))
            else:
                self.stdout.write(self.style.ERROR(f"Unknown service: {service}"))
        else:
            # Clear all RapidAPI cache entries
            # Since Django cache doesn't support pattern deletion, we'll iterate through known combinations
            cleared = 0
            for service_name in ["AppleMusic", "SoundCloud"]:
                if service_name not in SERVICE_CONFIGS:
                    continue
                config = SERVICE_CONFIGS[service_name]
                for genre_name in PLAYLIST_GENRES:
                    if genre_name not in config.get("links", {}):
                        continue

                    # Reconstruct URL
                    if service_name == "AppleMusic":
                        playlist_id = config["links"][genre_name].split("/")[-1]
                        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
                        url = f"{config['base_url']}?url={apple_playlist_url}"
                    elif service_name == "SoundCloud":
                        playlist_url = config["links"][genre_name]
                        url = f"{config['base_url']}?playlist={playlist_url}"
                    else:
                        continue

                    cache_key = get_cache_key(service_name, genre_name, url)
                    if cache.delete(cache_key):
                        cleared += 1

            self.stdout.write(self.style.SUCCESS(f"Cleared {cleared} RapidAPI cache entries"))

    def show_stats(self) -> None:
        """Show cache statistics"""
        self.stdout.write("RapidAPI Cache Statistics:")
        self.stdout.write(f"TTL: {CACHE_TTL // 86400} days")

        # Check which entries are cached
        cached_entries = []
        for service_name in ["AppleMusic", "SoundCloud"]:
            if service_name not in SERVICE_CONFIGS:
                continue
            config = SERVICE_CONFIGS[service_name]
            for genre_name in PLAYLIST_GENRES:
                if genre_name not in config.get("links", {}):
                    continue

                # Reconstruct URL
                if service_name == "AppleMusic":
                    playlist_id = config["links"][genre_name].split("/")[-1]
                    apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
                    url = f"{config['base_url']}?url={apple_playlist_url}"
                elif service_name == "SoundCloud":
                    playlist_url = config["links"][genre_name]
                    url = f"{config['base_url']}?playlist={playlist_url}"
                else:
                    continue

                cache_key = get_cache_key(service_name, genre_name, url)
                if cache.get(cache_key):
                    cached_entries.append(f"{service_name}/{genre_name}")

        if cached_entries:
            self.stdout.write(f"\nCached entries ({len(cached_entries)}):")
            for entry in cached_entries:
                self.stdout.write(f"  ✓ {entry}")
        else:
            self.stdout.write("\nNo cached entries found")
