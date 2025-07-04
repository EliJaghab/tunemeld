"""Minimal Django test to diagnose Railway issues"""

import os
import sys

print("\n=== MINIMAL DJANGO TEST ===")
print(f"Python: {sys.version}")
print(f"Current dir: {os.getcwd()}")
print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}")

try:
    import django

    print(f"Django version: {django.VERSION}")
except ImportError as e:
    print(f"ERROR: Cannot import Django: {e}")
    sys.exit(1)

try:
    from django.conf import settings

    print(f"Settings module: {settings.SETTINGS_MODULE}")
    print(f"DEBUG: {settings.DEBUG}")
    print("Django imports OK!")
except Exception as e:
    print(f"ERROR: Django settings failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("=== TEST PASSED ===\n")
