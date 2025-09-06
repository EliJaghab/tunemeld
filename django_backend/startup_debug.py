#!/usr/bin/env python3
"""Emergency startup debug script for Railway"""

import os
import sys
import traceback

print("\n" + "=" * 50)
print("RAILWAY STARTUP DEBUG v2")
print("=" * 50)
print("Timestamp:", os.popen("date").read().strip())

# Environment info
print("\nENVIRONMENT:")
print(f"Python: {sys.version}")
print(f"Path: {sys.path}")
print(f"CWD: {os.getcwd()}")
print(f"Files in CWD: {os.listdir('.')}")

# Django settings
print(f"\nDJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}")

# Try importing Django
try:
    print("\nImporting Django...")
    import django

    print(f"✓ Django {django.__version__} imported successfully")

    print("\nSetting up Django...")
    django.setup()
    print("✓ Django setup complete")

    print("\nTesting Django server...")
    print("✓ Django management imported")

    print("\n✅ ALL CHECKS PASSED - Django should start normally")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    print("\nFULL TRACEBACK:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("Starting Django server...")
print("=" * 50 + "\n")

# Start the server
os.system("python manage.py runserver 0.0.0.0:8000")
