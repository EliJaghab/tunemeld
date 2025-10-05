#!/usr/bin/env python3
"""
WSGI module for TuneMeld Django application.
This is the entry point for Vercel serverless functions.
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Add the backend directory to Python path for Vercel
backend_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Vercel expects the WSGI application to be named 'app'
app = get_wsgi_application()
# Keep backward compatibility
application = app
