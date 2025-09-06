#!/usr/bin/env python3
"""
Fix malformed Unicode data in existing playlist records.
"""

import os
import sys

import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from core.models.d_raw_playlist import RawPlaylistData  # noqa: E402
from core.utils.utils import clean_unicode_text  # noqa: E402


def fix_unicode_data():
    """Fix malformed Unicode in playlist metadata."""
    raw_playlists = RawPlaylistData.objects.all()

    updated_count = 0
    for playlist in raw_playlists:
        original_name = playlist.playlist_name
        original_desc = playlist.playlist_cover_description_text

        if original_name:
            cleaned_name = clean_unicode_text(original_name)
            if cleaned_name != original_name:
                print(f"Fixing playlist name: {original_name!r} -> {cleaned_name!r}")
                playlist.playlist_name = cleaned_name
                updated_count += 1

        if original_desc:
            cleaned_desc = clean_unicode_text(original_desc)
            if cleaned_desc != original_desc:
                print(f"Fixing description: {original_desc[:50]!r}... -> {cleaned_desc[:50]!r}...")
                playlist.playlist_cover_description_text = cleaned_desc
                updated_count += 1

        if playlist.playlist_name != original_name or playlist.playlist_cover_description_text != original_desc:
            playlist.save()

    print(f"Updated {updated_count} fields across {raw_playlists.count()} playlist records")


if __name__ == "__main__":
    fix_unicode_data()
