#!/usr/bin/env python
"""
Wipe PostgreSQL schema and migration history on production database.
This drops all Django tables and clears migration history to start fresh.
"""
import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.core.settings')
django.setup()

def wipe_schema():
    """Drop all Django tables and clear migration history."""
    with connection.cursor() as cursor:
        print("🗑️  Starting database schema wipe...")
        
        # Get all table names
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("ℹ️  No tables found to drop")
        else:
            print(f"📋 Found {len(tables)} tables to drop:")
            for table in tables:
                print(f"   - {table}")
            
            # Drop all tables (CASCADE to handle foreign key constraints)
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    print(f"✅ Dropped table: {table}")
                except Exception as e:
                    print(f"⚠️  Error dropping {table}: {e}")
        
        # Check for remaining sequences (from IDENTITY columns)
        cursor.execute("""
            SELECT sequencename 
            FROM pg_sequences 
            WHERE schemaname = 'public'
        """)
        sequences = [row[0] for row in cursor.fetchall()]
        
        if sequences:
            print(f"🔄 Dropping {len(sequences)} sequences...")
            for seq in sequences:
                try:
                    cursor.execute(f"DROP SEQUENCE IF EXISTS {seq} CASCADE")
                    print(f"✅ Dropped sequence: {seq}")
                except Exception as e:
                    print(f"⚠️  Error dropping sequence {seq}: {e}")
        
        print("✅ Database schema wiped successfully!")
        print("🔄 Database is ready for fresh migrations")

if __name__ == '__main__':
    confirmation = input("⚠️  This will DROP ALL TABLES in the database. Type 'WIPE' to confirm: ")
    if confirmation == 'WIPE':
        wipe_schema()
    else:
        print("❌ Operation cancelled")