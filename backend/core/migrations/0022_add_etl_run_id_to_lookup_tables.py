# Generated manually to add etl_run_id fields to Genre, Service, and Rank models

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_rename_models_to_play_count"),
    ]

    operations = [
        # Add etl_run_id field to Genre model
        migrations.AddField(
            model_name='genre',
            name='etl_run_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='ETL run identifier for blue-green deployments'),
        ),
        # Add etl_run_id field to Service model
        migrations.AddField(
            model_name='service',
            name='etl_run_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='ETL run identifier for blue-green deployments'),
        ),
        # Add etl_run_id field to Rank model
        migrations.AddField(
            model_name='rank',
            name='etl_run_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='ETL run identifier for blue-green deployments'),
        ),
        # Update unique constraints to include etl_run_id
        migrations.AlterUniqueTogether(
            name='genre',
            unique_together={('name', 'etl_run_id')},
        ),
        migrations.AlterUniqueTogether(
            name='service',
            unique_together={('name', 'etl_run_id')},
        ),
        migrations.AlterUniqueTogether(
            name='rank',
            unique_together={('name', 'etl_run_id')},
        ),
        # Add indexes for etl_run_id fields
        migrations.RunSQL(
            "CREATE INDEX idx_genres_etl_run_id ON genres(etl_run_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_genres_etl_run_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_services_etl_run_id ON services(etl_run_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_services_etl_run_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_ranks_etl_run_id ON ranks(etl_run_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_ranks_etl_run_id;"
        ),
    ]
