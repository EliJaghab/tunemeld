"""Debug function to test Django imports in Vercel."""


def handler(request):
    """Test basic imports step by step."""
    try:
        import os
        import sys
        from pathlib import Path

        # Add backend directory to Python path
        backend_dir = Path(__file__).parent.parent / "backend"
        sys.path.insert(0, str(backend_dir))

        # Set Django settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

        try:
            import django

            django.setup()
            return f"Django setup successful! Version: {django.get_version()}"
        except Exception as e:
            return f"Django setup failed: {e!s}"

    except Exception as e:
        return f"Basic imports failed: {e!s}"
