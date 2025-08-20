"""
Initialize Genre and Service lookup tables.
Simple command for deployment - no output, just initialization.
"""

from core.utils import initialize_lookup_tables
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize Genre and Service lookup tables"

    def handle(self, *args: object, **options: object) -> None:
        initialize_lookup_tables()
