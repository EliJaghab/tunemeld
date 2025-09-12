#!/usr/bin/env python
"""
Fix migration history inconsistency on Railway database.
Railway has 0006 applied but not 0005, causing dependency issues.
"""
import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.core.settings')
django.setup()

def fix_migration_history():
    """Mark migration 0005 as applied since the schema is already correct."""
    with connection.cursor() as cursor:
        # Check if migration 0005 is already marked as applied
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'core' AND name = '0005_track_id_alter_track_isrc_and_more'
        """)
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("❌ Migration 0005 is not marked as applied. Fixing...")
            # Insert the migration record to mark it as applied
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('core', '0005_track_id_alter_track_isrc_and_more', NOW())
            """)
            print("✅ Migration 0005 marked as applied")
        else:
            print("ℹ️  Migration 0005 is already marked as applied")
    
    print("✅ Migration history fixed!")

if __name__ == '__main__':
    fix_migration_history()