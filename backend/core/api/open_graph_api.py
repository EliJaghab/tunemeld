from core.models.genre_service import Genre


def get_default_og_metadata() -> dict[str, str]:
    """Get default Open Graph metadata for tunemeld site."""
    return {
        "og_title": "tunemeld",
        "og_description": "Discover trending music across Spotify, Apple Music, and SoundCloud",
    }


def get_genre_og_metadata(genre_name: str) -> dict[str, str]:
    """Get Open Graph metadata for a specific genre."""
    try:
        genre_obj = Genre.objects.get(name=genre_name)
        genre_display = genre_obj.display_name or genre_name.title()

        return {
            "og_title": f"tunemeld - {genre_display}",
            "og_description": f"Discover trending {genre_display} music across Spotify, Apple Music, and SoundCloud",
        }
    except Genre.DoesNotExist:
        return get_default_og_metadata()


def get_track_og_metadata(track_name: str, artist_name: str, service_display_name: str) -> dict[str, str]:
    """Get Open Graph metadata for a specific track."""
    og_title = f"{track_name} by {artist_name} - tunemeld"
    og_description = f"Listen to {track_name} by {artist_name} on {service_display_name}"

    return {
        "og_title": og_title,
        "og_description": og_description,
    }
