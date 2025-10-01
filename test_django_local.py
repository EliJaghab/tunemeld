#!/usr/bin/env python3
"""Local test for Django imports that mirrors Vercel serverless function behavior."""

import os
import sys
from pathlib import Path


def test_django_imports():
    """Test Django imports step by step like in Vercel function."""
    print("Testing Django imports locally...")

    try:
        # Step 1: Add backend to path (like in Vercel function)
        backend_dir = Path(__file__).parent / "backend"
        print(f"Adding to path: {backend_dir}")
        sys.path.insert(0, str(backend_dir))

        # Step 2: Set Django settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        print("Set DJANGO_SETTINGS_MODULE=core.settings")

        # Step 3: Test Django import
        try:
            import django

            django_version = django.get_version()
            print(f"✓ Django imported successfully: {django_version}")
        except Exception as e:
            print(f"✗ Django import failed: {e}")
            return False

        # Step 4: Test Django setup
        try:
            django.setup()
            print("✓ Django setup successful")
        except Exception as e:
            print(f"✗ Django setup failed: {e}")
            return False

        # Step 5: Test schema import
        try:
            from core.graphql.schema import schema

            schema_type = str(type(schema))
            print(f"✓ Schema imported successfully: {schema_type}")
        except Exception as e:
            print(f"✗ Schema import failed: {e}")
            return False

        print("\n🎉 ALL TESTS PASSED! Django should work in Vercel.")
        return True

    except Exception as e:
        print(f"✗ General error: {e}")
        return False


if __name__ == "__main__":
    test_django_imports()
