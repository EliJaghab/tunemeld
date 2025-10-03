import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Add the backend directory to Python path for Vercel
current_path = Path(__file__).parent
backend_path = current_path.parent
sys.path.insert(0, str(backend_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Vercel expects the WSGI application to be named 'app'
app = get_wsgi_application()

# Keep backward compatibility
application = app
