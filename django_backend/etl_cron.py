#!/usr/bin/env python
"""
Railway Cron Job for ETL Pipeline
Runs inside Railway's private network with direct database access
"""

import logging
import os
import subprocess
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_command(command, description):
    """Run a management command and log the output"""
    logger.info(f"Starting: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        logger.info(f"✅ Completed: {description}")
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        return False


def main():
    """Run the ETL pipeline stages"""
    logger.info("=" * 50)
    logger.info(f"ETL Pipeline started at {datetime.now()}")
    logger.info("=" * 50)

    # Ensure we're in the right directory
    os.chdir("/app/django_backend")

    # Pipeline stages
    stages = [
        ("python manage.py migrate", "Database migrations"),
        ("python manage.py a_init_lookup_tables", "Initialize lookup tables"),
        ("python manage.py b_raw_extract", "Extract raw playlist data"),
        ("python manage.py c_normalize_raw_playlists", "Normalize raw data"),
        ("python manage.py d_hydrate_tracks", "Hydrate tracks with ISRC"),
    ]

    # Run each stage
    for command, description in stages:
        if not run_command(command, description):
            logger.error(f"Pipeline failed at: {description}")
            sys.exit(1)

    # Log statistics
    logger.info("=" * 50)
    logger.info("ETL Pipeline completed successfully")
    run_command(
        "python manage.py shell -c \"from core.models import *; print(f'Tracks: {Track.objects.count()}')\"",
        "Final statistics",
    )


if __name__ == "__main__":
    main()
