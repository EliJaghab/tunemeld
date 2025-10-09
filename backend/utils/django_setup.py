import os

import django
from django.apps import apps


def setup_django_safe():
    """Safe Django setup that avoids populate() reentrancy for serverless functions."""
    if not apps.ready:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        try:
            django.setup()
        except RuntimeError as e:
            if "populate() isn't reentrant" in str(e):
                pass
            else:
                raise
