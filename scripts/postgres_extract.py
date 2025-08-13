#!/usr/bin/env python3
"""
PostgreSQL Extraction Script for TuneMeld

Parallel ETL process that extracts raw playlist data and writes to PostgreSQL
instead of MongoDB. Uses the existing RapidAPI extraction logic but saves
to Django models.

Usage:
    python scripts/postgres_extract.py --help
    python scripts/postgres_extract.py --service=Spotify --genre=rap
    python scripts/postgres_extract.py --all
    python scripts/postgres_extract.py --dry-run
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.core.settings")

import django  # noqa: E402

django.setup()

# Now import Django models and playlist ETL modules
from django_backend.core.models import ETLRun, Genre, RawPlaylistData, Service  # noqa: E402
from playlist_etl.extract import (  # noqa: E402
    PLAYLIST_GENRES,
    SERVICE_CONFIGS,
    AppleMusicFetcher,
    RapidAPIClient,
    SoundCloudFetcher,
    SpotifyFetcher,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PostgreSQLExtractor:
    """Extracts playlist data and writes to PostgreSQL using Django models."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.client = RapidAPIClient()

        # Statistics
        self.extracted_count = 0
        self.error_count = 0

    def extract_single(self, service_name: str, genre_name: str) -> bool:
        """Extract data for a single service/genre combination."""

        try:
            # Get or create Django model instances
            service, created = Service.objects.get_or_create(
                name=service_name, defaults={"display_name": service_name, "is_track_source": True}
            )
            if created:
                logger.info(f"Created new service: {service_name}")

            genre, created = Genre.objects.get_or_create(name=genre_name, defaults={"display_name": genre_name.title()})
            if created:
                logger.info(f"Created new genre: {genre_name}")

            # Start ETL run tracking
            etl_run = ETLRun.objects.create(stage="extract", service=service, genre=genre, status="running")

            try:
                # Create appropriate extractor
                if service_name == "AppleMusic":
                    extractor = AppleMusicFetcher(self.client, service_name, genre_name)
                elif service_name == "SoundCloud":
                    extractor = SoundCloudFetcher(self.client, service_name, genre_name)
                elif service_name == "Spotify":
                    extractor = SpotifyFetcher(self.client, service_name, genre_name)
                else:
                    raise ValueError(f"Unknown service: {service_name}")

                # Extract playlist metadata and data
                logger.info(f"Extracting {service_name} {genre_name} playlist...")
                extractor.set_playlist_details()
                playlist_data = extractor.get_playlist()

                if self.dry_run:
                    logger.info(f"DRY RUN: Would save {service_name}/{genre_name} data")
                    logger.info(f"Playlist: {extractor.playlist_name}")
                    logger.info(f"Tracks: {len(playlist_data.get('tracks', []))}")
                    self.extracted_count += 1
                else:
                    # Save to PostgreSQL
                    raw_data = RawPlaylistData(
                        genre=genre,
                        service=service,
                        playlist_url=extractor.playlist_url,
                        playlist_name=extractor.playlist_name,
                        playlist_cover_url=extractor.playlist_cover_url,
                        playlist_cover_description_text=extractor.playlist_cover_description_text,
                        playlist_tagline=getattr(extractor, "playlist_tagline", None),
                        playlist_featured_artist=getattr(extractor, "playlist_featured_artist", None),
                        playlist_saves_count=getattr(extractor, "playlist_saves_count", None),
                        playlist_track_count=getattr(extractor, "playlist_track_count", None),
                        playlist_creator=getattr(extractor, "playlist_creator", None),
                        data=playlist_data,
                        processed=False,
                    )
                    raw_data.save()

                    logger.info(f"✅ Saved {service_name}/{genre_name}: {extractor.playlist_name}")
                    logger.info(f"   Tracks: {len(playlist_data.get('tracks', []))}")
                    logger.info(f"   ID: {raw_data.id}")

                    self.extracted_count += 1
                    etl_run.records_processed = 1

                # Mark ETL run as completed
                etl_run.status = "completed"
                etl_run.save()

                return True

            except Exception as e:
                # Mark ETL run as failed
                etl_run.status = "failed"
                etl_run.error_message = str(e)
                etl_run.save()
                raise

        except Exception as e:
            logger.error(f"❌ Failed to extract {service_name}/{genre_name}: {e}")
            self.error_count += 1
            return False

    def extract_all(self) -> None:
        """Extract data for all service/genre combinations."""

        logger.info("Starting extraction for all services and genres...")

        total_combinations = len(SERVICE_CONFIGS) * len(PLAYLIST_GENRES)
        logger.info(f"Total combinations to process: {total_combinations}")

        for service_name in SERVICE_CONFIGS:
            for genre_name in PLAYLIST_GENRES:
                logger.info(f"Processing {service_name}/{genre_name}...")
                self.extract_single(service_name, genre_name)

        logger.info("Extraction complete!")
        logger.info(f"✅ Successfully extracted: {self.extracted_count}")
        logger.info(f"❌ Errors: {self.error_count}")

    def get_recent_data(self, limit: int = 10) -> None:
        """Display recent extracted data."""

        recent_data = RawPlaylistData.objects.select_related("service", "genre").order_by("-created_at")[:limit]

        if not recent_data:
            print("No raw playlist data found.")
            return

        print(f"\nRecent {len(recent_data)} extractions:")
        print("=" * 80)

        for data in recent_data:
            status = "✅ Processed" if data.processed else "⏳ Pending"
            track_count = len(data.data.get("tracks", []))
            print(
                f"{data.created_at.strftime('%Y-%m-%d %H:%M')} | {data.service.name:12} | "
                f"{data.genre.name:8} | {track_count:3} tracks | {status}"
            )
            print(f"  📝 {data.playlist_name}")
            print(f"  🔗 {data.playlist_url}")
            print()


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL Playlist Data Extraction")
    parser.add_argument(
        "--service", choices=list(SERVICE_CONFIGS.keys()), help="Extract data for specific service only"
    )
    parser.add_argument("--genre", choices=PLAYLIST_GENRES, help="Extract data for specific genre only")
    parser.add_argument("--all", action="store_true", help="Extract data for all services and genres")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted without saving")
    parser.add_argument("--recent", type=int, default=0, metavar="N", help="Show N most recent extractions and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    extractor = PostgreSQLExtractor(dry_run=args.dry_run)

    # Show recent data and exit
    if args.recent:
        extractor.get_recent_data(args.recent)
        return

    # Validate arguments
    if args.service and not args.genre:
        parser.error("--service requires --genre to be specified")
    if args.genre and not args.service:
        parser.error("--genre requires --service to be specified")
    if not args.all and not (args.service and args.genre):
        parser.error("Must specify either --all or both --service and --genre")

    try:
        if args.all:
            extractor.extract_all()
        else:
            success = extractor.extract_single(args.service, args.genre)
            if success:
                print(f"✅ Successfully extracted {args.service}/{args.genre}")
            else:
                print(f"❌ Failed to extract {args.service}/{args.genre}")
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error during extraction")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
