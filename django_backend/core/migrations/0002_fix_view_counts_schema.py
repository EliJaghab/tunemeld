# Generated manually for view count schema fix - PostgreSQL optimized
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Drop existing view_counts table if it exists
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS view_counts CASCADE;",
            reverse_sql="-- Cannot reverse this operation"
        ),

        # Create view_counts table with PostgreSQL syntax
        migrations.RunSQL(
            sql="""
                CREATE TABLE view_counts (
                    id SERIAL PRIMARY KEY,
                    isrc VARCHAR(12) NOT NULL,
                    service_id INTEGER NOT NULL REFERENCES services(id) DEFERRABLE INITIALLY DEFERRED,
                    view_count BIGINT NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    CONSTRAINT view_counts_unique_isrc_service UNIQUE (isrc, service_id)
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS view_counts CASCADE;"
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
            sql="ALTER TABLE historical_view_counts ADD COLUMN IF NOT EXISTS delta_count BIGINT;",
            reverse_sql="-- Cannot reverse: PostgreSQL doesn't support conditional DROP COLUMN"
        ),
    ]
