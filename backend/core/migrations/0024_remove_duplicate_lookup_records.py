# Remove duplicate Genre, Service, and Rank records created by ETL run ID changes

from django.db import migrations


def remove_duplicates(apps, schema_editor):
    """Remove legacy records without etl_run_id to fix duplicates."""
    Genre = apps.get_model('core', 'Genre')
    Service = apps.get_model('core', 'Service')
    Rank = apps.get_model('core', 'Rank')

    # Only delete records that don't have etl_run_id (legacy records)
    # Keep the newer records that have etl_run_id values

    # Remove legacy Genres without etl_run_id
    legacy_genres = Genre.objects.filter(etl_run_id__isnull=True)
    legacy_genre_count = legacy_genres.count()
    legacy_genres.delete()

    # Remove legacy Services without etl_run_id
    legacy_services = Service.objects.filter(etl_run_id__isnull=True)
    legacy_service_count = legacy_services.count()
    legacy_services.delete()

    # Remove legacy Ranks without etl_run_id
    legacy_ranks = Rank.objects.filter(etl_run_id__isnull=True)
    legacy_rank_count = legacy_ranks.count()
    legacy_ranks.delete()

    print(f"Removed {legacy_genre_count} legacy Genre records")
    print(f"Removed {legacy_service_count} legacy Service records")
    print(f"Removed {legacy_rank_count} legacy Rank records")


def reverse_remove_duplicates(apps, schema_editor):
    """Cannot reverse duplicate removal - this is a destructive operation."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_fix_unique_constraints_for_etl_run_id"),
    ]

    operations = [
        # Clean up duplicate records
        migrations.RunPython(
            remove_duplicates,
            reverse_remove_duplicates
        ),
    ]
