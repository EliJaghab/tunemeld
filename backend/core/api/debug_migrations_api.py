"""
Debug endpoint to check database migration status and indexes.
"""

from django.db import connection
from django.http import JsonResponse


def debug_migrations_status(request):
    """Check applied migrations and database indexes."""
    try:
        with connection.cursor() as cursor:
            # Check applied migrations
            cursor.execute("""
                SELECT app, name, applied
                FROM django_migrations
                WHERE app = 'core'
                ORDER BY applied DESC
                LIMIT 10
            """)
            migrations = []
            for row in cursor.fetchall():
                migrations.append({"app": row[0], "name": row[1], "applied": row[2].isoformat() if row[2] else None})

            # Check if our critical indexes exist
            cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND (
                    indexname LIKE '%genre_i_%'
                    OR indexname LIKE '%playlists_genre_i_%'
                    OR indexname LIKE '%raw_playlis_genre_i_%'
                )
                ORDER BY indexname
            """)
            indexes = []
            for row in cursor.fetchall():
                indexes.append({"index_name": row[0], "table_name": row[1]})

            # Check table row counts
            cursor.execute("SELECT COUNT(*) FROM core_rawplaylistdatamodel")
            raw_playlist_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM core_playlistmodel")
            playlist_count = cursor.fetchone()[0]

            return JsonResponse(
                {
                    "status": "success",
                    "migrations": migrations,
                    "critical_indexes": indexes,
                    "table_counts": {"raw_playlists": raw_playlist_count, "playlists": playlist_count},
                    "database_info": {
                        "vendor": connection.vendor,
                        "version": str(connection.pg_version) if hasattr(connection, "pg_version") else "unknown",
                    },
                }
            )

    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e), "error_type": type(e).__name__}, status=500)
