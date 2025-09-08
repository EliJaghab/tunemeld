# Generated manually for view count schema fix
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # First, drop the existing view_counts table entirely
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS view_counts;",
            reverse_sql="-- Cannot reverse this operation"
        ),

        # Recreate view_counts table with proper schema
        migrations.RunSQL(
            sql="""
                CREATE TABLE view_counts (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    isrc VARCHAR(12) NOT NULL,
                    service_id INTEGER NOT NULL REFERENCES services(id) DEFERRABLE INITIALLY DEFERRED,
                    view_count BIGINT NOT NULL,
                    last_updated DATETIME NOT NULL,
                    created_at DATETIME NOT NULL,
                    CONSTRAINT view_counts_unique_isrc_service UNIQUE (isrc, service_id)
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS view_counts;"
        ),

        # Create indexes for performance
        migrations.RunSQL(
            sql="""
                CREATE INDEX view_counts_isrc_idx ON view_counts(isrc);
                CREATE INDEX view_counts_service_id_idx ON view_counts(service_id);
                CREATE INDEX view_counts_last_updated_idx ON view_counts(last_updated);
                CREATE INDEX view_counts_view_count_idx ON view_counts(view_count DESC);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS view_counts_isrc_idx;
                DROP INDEX IF EXISTS view_counts_service_id_idx;
                DROP INDEX IF EXISTS view_counts_last_updated_idx;
                DROP INDEX IF EXISTS view_counts_view_count_idx;
            """
        ),

        # Add delta_count field to historical_view_counts if it doesn't exist
        migrations.RunSQL(
            sql="ALTER TABLE historical_view_counts ADD COLUMN delta_count BIGINT;",
            reverse_sql="-- SQLite doesn't support DROP COLUMN"
        ),
    ]
