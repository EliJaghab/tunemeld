"""
API functions for playlist data operations.

Provides utilities for retrieving playlist-specific data for cache warming
and other operations that need to work with actual playlist tracks.
"""

from core.models.playlist import PlaylistModel


def get_playlist_isrcs(service_name: str) -> list[str]:
    return list(
        PlaylistModel.objects.filter(isrc__isnull=False, service__name=service_name)
        .values_list("isrc", flat=True)
        .distinct()
    )


def get_playlist_isrcs_by_service(service_name: str) -> list[str]:
    """
    Get unique ISRCs from tracks in playlists for a specific service.

    Args:
        service_name: Name of the service (e.g., 'spotify', 'apple_music')

    Returns:
        List of unique ISRC codes for tracks in the specified service's playlists
    """
    return list(
        PlaylistModel.objects.filter(isrc__isnull=False, service__name=service_name)
        .values_list("isrc", flat=True)
        .distinct()
    )


def get_playlist_isrcs_by_genre(genre_name: str) -> list[str]:
    """
    Get unique ISRCs from tracks in playlists for a specific genre.

    Args:
        genre_name: Name of the genre

    Returns:
        List of unique ISRC codes for tracks in the specified genre's playlists
    """
    return list(
        PlaylistModel.objects.filter(isrc__isnull=False, genre__name=genre_name)
        .values_list("isrc", flat=True)
        .distinct()
    )
