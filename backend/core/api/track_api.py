from core.api.genre_service_api import get_genre, get_service, get_track_by_isrc
from core.api.open_graph_api import get_default_og_metadata, get_genre_og_metadata, get_track_og_metadata
from core.constants import GenreName, ServiceName
from core.models.track import TrackModel
from core.utils.track_similarity import get_similar_tracks as get_similar_tracks_util


def validate_track_url_params(genre: str, rank: str, player: str | None, isrc: str) -> dict:
    """
    Validate track URL parameters for server-side rendering.

    Used when someone navigates to a track URL to verify all parameters are valid.
    This does NOT build URLs - it validates existing URLs that were built by GraphQL.

    Returns:
        Dict with validation results and validated objects
    """
    result: dict = {
        "valid": False,
        "genre_obj": None,
        "service_obj": None,
        "track_obj": None,
        "player": None,
    }

    if not (genre and isrc):
        return result

    genre_enum = GenreName(genre)
    genre_obj = get_genre(genre_enum)
    if not genre_obj:
        return result
    result["genre_obj"] = genre_obj

    track_obj = get_track_by_isrc(isrc)
    if not track_obj:
        return result
    result["track_obj"] = track_obj

    if player:
        try:
            service_name = ServiceName(player)
            service_obj = get_service(service_name)
            if service_obj:
                result["service_obj"] = service_obj
                result["player"] = player
        except (ValueError, TypeError):
            pass

    result["valid"] = True
    return result


def get_track_metadata(genre: str, rank: str, player: str | None, isrc: str) -> dict:
    """
    Get track metadata for social sharing previews (Open Graph data).

    Flow: GraphQL builds URL → User clicks/shares URL → Django calls this function
    → Returns data for rich preview cards (title, description, image) when shared
    on Discord, Twitter, etc.

    This does NOT build URLs or handle player switching - it creates sharing previews.

    Returns:
        Dict with track data and Open Graph metadata for HTML meta tags
    """
    validation = validate_track_url_params(genre, rank, player, isrc)

    if not validation["valid"]:
        default_og = get_default_og_metadata()
        return {
            "valid": False,
            "track_data": None,
            "og_image": None,
            **default_og,
        }

    track = validation["track_obj"]
    genre_obj = validation["genre_obj"]
    service_obj = validation["service_obj"]

    track_data = {
        "isrc": track.isrc,
        "track_name": track.track_name,
        "artist_name": track.artist_name,
        "album_cover_url": track.album_cover_url,
    }

    service_display_name = service_obj.display_name if service_obj else genre_obj.display_name or genre_obj.name
    og_metadata = get_track_og_metadata(track.track_name, track.artist_name, service_display_name)

    return {
        "valid": True,
        "track_data": track_data,
        "og_image": track.album_cover_url,
        "player": validation["player"],
        **og_metadata,
    }


def get_genre_metadata(genre: str) -> dict:
    """Get metadata for genre-only URLs for social sharing previews."""
    genre_enum = GenreName(genre)
    genre_obj = get_genre(genre_enum)
    if genre_obj:
        og_metadata = get_genre_og_metadata(genre)
        return {
            "valid": True,
            **og_metadata,
        }

    og_metadata = get_default_og_metadata()
    return {
        "valid": False,
        **og_metadata,
    }


def build_track_query_url(genre: str, rank: str, isrc: str, player: str) -> str | None:
    """
    Build shareable track URLs for GraphQL API responses.

    Called by GraphQL to generate the trackDetailUrlSpotify, trackDetailUrlAppleMusic, etc.
    fields that the frontend uses for track title links and navigation.

    Flow: Frontend requests tracks → GraphQL calls this → Returns shareable URLs
    → User clicks URL → Django processes it with get_track_metadata()

    Example: /?genre=pop&rank=tunemeld-rank&player=spotify&isrc=USRC12502004

    Returns:
        Shareable URL string, or None if player is invalid
    """
    try:
        service_name = ServiceName(player)
        service = get_service(service_name)
        if service:
            return f"/?genre={genre}&rank={rank}&player={player}&isrc={isrc}"
    except (ValueError, TypeError):
        pass

    return None


def get_similar_tracks(isrc: str, limit: int = 10) -> list[dict[str, str | float]]:
    """
    Get tracks similar to the given track based on audio features.

    Args:
        isrc: Source track ISRC
        limit: Maximum number of similar tracks to return (default: 10)

    Returns:
        List of dicts with track metadata and similarity scores, ranked by similarity
        Example: [
            {
                "isrc": "GBUM72504512",
                "track_name": "Blessings",
                "artist_name": "Calvin Harris",
                "similarity_score": 0.9816
            },
            ...
        ]

    Raises:
        ValueError: If track not found or has no audio features
    """
    if not TrackModel.objects.filter(isrc=isrc).exists():
        raise ValueError(f"Track with ISRC {isrc} not found")

    results = get_similar_tracks_util(isrc=isrc, limit=limit)

    if not results:
        raise ValueError("No similar tracks found (track may not have audio features)")

    return results
