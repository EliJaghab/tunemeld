"""
Django management command to populate Genre and Service lookup tables.
Run with: python manage.py populate_lookup_tables

This command is idempotent - it can be run multiple times safely.
"""

from core.models import Genre, Service
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Populates the Genre and Service lookup tables with initial data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating it",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        self.stdout.write("Populating lookup tables...")

        genres_created = 0
        genres_existing = 0
        services_created = 0
        services_existing = 0

        with transaction.atomic():
            # Genre data
            genres = [
                {"name": "dance", "display_name": "Dance/Electronic"},
                {"name": "rap", "display_name": "Hip-Hop/Rap"},
                {"name": "country", "display_name": "Country"},
                {"name": "pop", "display_name": "Pop"},
            ]

            self.stdout.write("\nProcessing genres:")
            for genre_data in genres:
                if dry_run:
                    try:
                        existing = Genre.objects.get(name=genre_data["name"])
                        self.stdout.write(f"  - Would skip existing: {existing.display_name}")
                        genres_existing += 1
                    except Genre.DoesNotExist:
                        self.stdout.write(f'  + Would create: {genre_data["display_name"]} ({genre_data["name"]})')
                        genres_created += 1
                else:
                    genre, created = Genre.objects.get_or_create(
                        name=genre_data["name"], defaults={"display_name": genre_data["display_name"]}
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'  Created genre: {genre.display_name} ({genre_data["name"]})')
                        )
                        genres_created += 1
                    else:
                        self.stdout.write(f"  - Genre already exists: {genre.display_name}")
                        genres_existing += 1

            services = [
                {
                    "name": "Spotify",
                    "display_name": "Spotify",
                    "is_track_source": True,
                    "is_data_source": True,
                },
                {
                    "name": "SoundCloud",
                    "display_name": "SoundCloud",
                    "is_track_source": True,
                    "is_data_source": False,
                },
                {
                    "name": "AppleMusic",
                    "display_name": "Apple Music",
                    "is_track_source": True,
                    "is_data_source": False,
                },
                {
                    "name": "YouTube",
                    "display_name": "YouTube",
                    "is_track_source": False,
                    "is_data_source": True,
                },
            ]

            self.stdout.write("\nProcessing services:")
            for service_data in services:
                if dry_run:
                    try:
                        existing = Service.objects.get(name=service_data["name"])
                        self.stdout.write(f"  - Would skip existing: {existing.display_name}")
                        services_existing += 1
                    except Service.DoesNotExist:
                        source_type = []
                        if service_data["is_track_source"]:
                            source_type.append("track source")
                        if service_data["is_data_source"]:
                            source_type.append("data source")
                        type_str = "+".join(source_type)
                        self.stdout.write(f'  + Would create: {service_data["display_name"]} ({type_str})')
                        services_created += 1
                else:
                    service, created = Service.objects.get_or_create(
                        name=service_data["name"],
                        defaults={
                            "display_name": service_data["display_name"],
                            "is_track_source": service_data["is_track_source"],
                            "is_data_source": service_data["is_data_source"],
                        },
                    )
                    if created:
                        source_type = []
                        if service_data["is_track_source"]:
                            source_type.append("track source")
                        if service_data["is_data_source"]:
                            source_type.append("data source")
                        type_str = "+".join(source_type) if source_type else "no sources"
                        self.stdout.write(self.style.SUCCESS(f"  Created service: {service.display_name} ({type_str})"))
                        services_created += 1
                    else:
                        self.stdout.write(f"  - Service already exists: {service.display_name}")
                        services_existing += 1

        self.stdout.write("\nSummary:")
        self.stdout.write(f"  Genres: {genres_created} created, {genres_existing} existing")
        self.stdout.write(f"  Services: {services_created} created, {services_existing} existing")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN COMPLETE - No changes were made"))
        elif genres_created == 0 and services_created == 0:
            self.stdout.write(self.style.SUCCESS("\nLookup tables already up to date!"))
        else:
            self.stdout.write(self.style.SUCCESS("\nLookup tables populated successfully!"))

        total_genres = Genre.objects.count()
        total_services = Service.objects.count()
        self.stdout.write(f"\nFinal state: {total_genres} genres, {total_services} services in database")
