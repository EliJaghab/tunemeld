from core.api.open_graph_api import get_default_og_metadata
from core.api.track_metadata_api import get_genre_metadata, get_track_metadata
from django.shortcuts import render


def main_view(request):
    """
    Main Django view for server-side rendering and social sharing.

    Handles URLs built by GraphQL API and generates HTML with proper Open Graph
    meta tags for rich previews when shared on social media.

    Supported URL formats:
    1. Genre/rank only: /?genre=pop&rank=tunemeld-rank
    2. Track URLs: /?genre=pop&rank=tunemeld-rank&player=spotify&isrc=USRC12502004

    Flow: GraphQL builds URLs → User navigates/shares URL → This view renders HTML
    → Creates rich preview cards on Discord/Twitter/etc.
    """
    genre = request.GET.get("genre")
    rank = request.GET.get("rank")
    player = request.GET.get("player")
    isrc = request.GET.get("isrc")

    default_og = get_default_og_metadata()
    context = {
        "genre": genre,
        "rank": rank,
        "player": player,
        "isrc": isrc,
        "track_data": None,
        "og_url": request.build_absolute_uri(),
        **default_og,
    }

    # Handle track URLs
    if isrc and genre:
        track_metadata = get_track_metadata(genre, rank, player, isrc)
        if track_metadata["valid"]:
            context.update(
                {
                    "track_data": track_metadata["track_data"],
                    "og_title": track_metadata["og_title"],
                    "og_description": track_metadata["og_description"],
                    "og_image": track_metadata["og_image"],
                    "player": track_metadata["player"],
                }
            )

    # Handle genre-only URLs (if no track data was loaded)
    elif genre and not context.get("track_data"):
        genre_metadata = get_genre_metadata(genre)
        if genre_metadata["valid"]:
            context.update(
                {
                    "og_title": genre_metadata["og_title"],
                    "og_description": genre_metadata["og_description"],
                }
            )

    return render(request, "index.html", context)
