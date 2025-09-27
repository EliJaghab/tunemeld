from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fake apply migration 0027 if aggregate_play_counts table already exists"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'aggregate_play_counts'
                );
            """)
            table_exists = cursor.fetchone()[0]

            # Check if migration 0027 is already recorded
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations
                WHERE app = 'core' AND name = '0027_remove_etl_run_id_from_genre_service';
            """)
            migration_exists = cursor.fetchone()[0] > 0

            if table_exists and not migration_exists:
                # Mark migration 0027 as applied
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('core', '0027_remove_etl_run_id_from_genre_service', NOW());
                """)
                self.stdout.write(
                    self.style.SUCCESS("Successfully marked migration 0027 as applied (table already exists)")
                )
            elif migration_exists:
                self.stdout.write("Migration 0027 is already marked as applied")
            else:
                self.stdout.write("Table doesn't exist, migration 0027 should run normally")
