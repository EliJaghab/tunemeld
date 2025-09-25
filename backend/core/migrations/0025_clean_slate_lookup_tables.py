# Drop and recreate lookup tables to eliminate all duplicate records

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_remove_duplicate_lookup_records"),
    ]

    operations = [
        # Clear all ETL-related data that depends on lookup tables
        migrations.RunSQL(
            "DELETE FROM raw_playlist_data;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM service_tracks;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM playlists;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM tracks;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM historical_track_play_counts;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM aggregate_play_counts;",
            reverse_sql="-- Cannot restore deleted data"
        ),

        # Clear lookup tables completely
        migrations.RunSQL(
            "DELETE FROM genres;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM services;",
            reverse_sql="-- Cannot restore deleted data"
        ),
        migrations.RunSQL(
            "DELETE FROM ranks;",
            reverse_sql="-- Cannot restore deleted data"
        ),

        # Reset auto-increment sequences to start fresh
        migrations.RunSQL(
            "ALTER SEQUENCE genres_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE services_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE ranks_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE raw_playlist_data_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE service_tracks_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE playlists_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE tracks_id_seq RESTART WITH 1;",
            reverse_sql="-- Cannot restore sequence state"
        ),
    ]
