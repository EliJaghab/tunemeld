"""Vercel serverless entry point that configures Django WSGI without modifying sys.path."""

import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent / "backend"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("PYTHONPATH", str(backend_dir))

import django  # noqa: E402

django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
