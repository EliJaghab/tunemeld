# Fix unique constraints for etl_run_id fields in lookup tables

import uuid
from django.db import migrations, models


def populate_etl_run_id(apps, schema_editor):
    """Populate etl_run_id for existing records with a single UUID."""
    Genre = apps.get_model('core', 'Genre')
    Service = apps.get_model('core', 'Service')
    Rank = apps.get_model('core', 'Rank')

    # Use a single ETL run ID for all existing records
    legacy_etl_run_id = uuid.uuid4()

    # Update all existing records that don't have etl_run_id
    Genre.objects.filter(etl_run_id__isnull=True).update(etl_run_id=legacy_etl_run_id)
    Service.objects.filter(etl_run_id__isnull=True).update(etl_run_id=legacy_etl_run_id)
    Rank.objects.filter(etl_run_id__isnull=True).update(etl_run_id=legacy_etl_run_id)


def reverse_populate_etl_run_id(apps, schema_editor):
    """Clear etl_run_id for existing records."""
    Genre = apps.get_model('core', 'Genre')
    Service = apps.get_model('core', 'Service')
    Rank = apps.get_model('core', 'Rank')

    Genre.objects.all().update(etl_run_id=None)
    Service.objects.all().update(etl_run_id=None)
    Rank.objects.all().update(etl_run_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_add_etl_run_id_to_lookup_tables"),
    ]

    operations = [
        # First, remove the old unique constraints that are causing conflicts
        migrations.RunSQL(
            "ALTER TABLE genres DROP CONSTRAINT IF EXISTS genres_name_key;",
            reverse_sql="ALTER TABLE genres ADD CONSTRAINT genres_name_key UNIQUE (name);"
        ),
        migrations.RunSQL(
            "ALTER TABLE services DROP CONSTRAINT IF EXISTS services_name_key;",
            reverse_sql="ALTER TABLE services ADD CONSTRAINT services_name_key UNIQUE (name);"
        ),
        migrations.RunSQL(
            "ALTER TABLE ranks DROP CONSTRAINT IF EXISTS ranks_name_key;",
            reverse_sql="ALTER TABLE ranks ADD CONSTRAINT ranks_name_key UNIQUE (name);"
        ),

        # Populate etl_run_id for existing records
        migrations.RunPython(
            populate_etl_run_id,
            reverse_populate_etl_run_id
        ),

        # Make etl_run_id required (remove null=True that was implicit before)
        migrations.AlterField(
            model_name='genre',
            name='etl_run_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='ETL run identifier for blue-green deployments'),
        ),
        migrations.AlterField(
            model_name='service',
            name='etl_run_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='ETL run identifier for blue-green deployments'),
        ),
        migrations.AlterField(
            model_name='rank',
            name='etl_run_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='ETL run identifier for blue-green deployments'),
        ),
    ]
