import graphene
from core.constants import GENRE_CONFIGS, RANK_CONFIGS, SERVICE_CONFIGS, SERVICE_RANK_FIELDS, RankType, ServiceName
from domain_types.types import ButtonLabel


class ButtonLabelType(graphene.ObjectType):
    button_type = graphene.String(required=True, description="Type of button (e.g., 'source_icon', 'genre_button')")
    context = graphene.String(description="Context identifier for the button")
    title = graphene.String(description="Tooltip text for the button")
    aria_label = graphene.String(description="Screen reader accessible label")


def generate_track_button_labels(track, genre=None, service=None):
    """
    Generate contextual button labels for track-related buttons.
    Returns full track names and service-specific context.
    """
    labels = []

    full_track_name = track.track_name or "Unknown Track"
    full_artist_name = track.artist_name or "Unknown Artist"
    full_track_display = f"'{full_track_name}' by {full_artist_name}"

    # Service source icon buttons
    service_sources = [
        (ServiceName.SPOTIFY.value, track.spotify_url, SERVICE_RANK_FIELDS[ServiceName.SPOTIFY.value]),
        (ServiceName.APPLE_MUSIC.value, track.apple_music_url, SERVICE_RANK_FIELDS[ServiceName.APPLE_MUSIC.value]),
        (ServiceName.SOUNDCLOUD.value, track.soundcloud_url, SERVICE_RANK_FIELDS[ServiceName.SOUNDCLOUD.value]),
        (ServiceName.YOUTUBE.value, track.youtube_url, SERVICE_RANK_FIELDS[ServiceName.YOUTUBE.value]),
    ]

    for service_name, url, rank_field in service_sources:
        if url and service_name in SERVICE_CONFIGS:
            service_config = SERVICE_CONFIGS[service_name]
            display_name = service_config["display_name"]

            # Get rank if available
            rank_text = ""
            if rank_field and hasattr(track, rank_field):
                rank = getattr(track, rank_field)
                if rank:
                    rank_text = f" (Rank #{rank})"

            labels.append(
                ButtonLabel(
                    button_type="source_icon",
                    context=service_name,
                    title=f"Play {full_track_display} on {display_name}{rank_text}",
                    aria_label=f"Play {full_track_name} by {full_artist_name} on {display_name}",
                )
            )

    return labels


def generate_genre_button_labels(genre_name):
    """Generate contextual labels for genre filter buttons."""
    if genre_name not in GENRE_CONFIGS:
        return []

    genre_config = GENRE_CONFIGS[genre_name]
    display_name = genre_config["display_name"]

    # Get available services for this genre
    available_services = []
    if "links" in genre_config:
        for service_name in genre_config["links"]:
            if service_name in SERVICE_CONFIGS:
                available_services.append(SERVICE_CONFIGS[service_name]["display_name"])

    if available_services:
        services_text = ", ".join(available_services)
        title = f"View {display_name} tracks from {services_text}"
        aria_label = f"Filter to show {display_name} genre tracks"
    else:
        title = f"View {display_name} tracks"
        aria_label = f"Filter to show {display_name} genre"

    return [ButtonLabel(button_type="genre_button", context=genre_name, title=title, aria_label=aria_label)]


def generate_rank_button_labels(rank_type):
    """Generate contextual labels for ranking/sorting buttons."""
    if rank_type not in RANK_CONFIGS:
        return []

    rank_config = RANK_CONFIGS[rank_type]
    display_name = rank_config["display_name"]
    sort_order = rank_config["sort_order"]
    if rank_type == RankType.TUNEMELD_RANK.value:
        title = "Sort by TuneMeld algorithm (cross-platform popularity ranking)"
        aria_label = "Sort tracks by TuneMeld ranking algorithm"
    elif rank_type == RankType.TOTAL_PLAYS_RANK.value:
        order_desc = "most to least" if sort_order == "desc" else "least to most"
        title = f"Sort by Total Plays ({order_desc} played across all platforms)"
        aria_label = "Sort tracks by total play count"
    elif rank_type == RankType.TRENDING_RANK.value:
        title = "Sort by Trending (biggest weekly growth in plays)"
        aria_label = "Sort tracks by trending growth"
    else:
        title = f"Sort by {display_name}"
        aria_label = f"Sort tracks by {display_name}"

    return [ButtonLabel(button_type="rank_button", context=rank_type, title=title, aria_label=aria_label)]


def generate_service_button_labels(service_name, track_name=None):
    """Generate labels for service player switching buttons."""
    if service_name not in SERVICE_CONFIGS:
        return []

    service_config = SERVICE_CONFIGS[service_name]
    display_name = service_config["display_name"]

    if track_name:
        title = f"Switch to {display_name} player for '{track_name}'"
        aria_label = f"Play {track_name} on {display_name}"
    else:
        title = f"Play on {display_name}"
        aria_label = f"Switch to {display_name} player"

    return [ButtonLabel(button_type="service_player_button", context=service_name, title=title, aria_label=aria_label)]


def generate_playlist_button_labels(playlist_type, is_collapsed=False, track_count=None):
    """Generate labels for playlist collapse/expand buttons."""
    action = "Show" if is_collapsed else "Hide"

    if playlist_type == "main":
        playlist_name = "TuneMeld main playlist"
    elif playlist_type in SERVICE_CONFIGS:
        service_display = SERVICE_CONFIGS[playlist_type]["display_name"]
        playlist_name = f"{service_display} playlist"
    else:
        raise ValueError(f"Invalid playlist_type '{playlist_type}' in generate_playlist_button_labels")

    track_info = f" ({track_count} tracks)" if track_count else ""

    return [
        ButtonLabelType(
            button_type="collapse_button",
            context=f"{playlist_type}_{'collapsed' if is_collapsed else 'expanded'}",
            title=f"{action} {playlist_name}{track_info}",
            aria_label=f"{action} {playlist_name}",
        )
    ]


def generate_misc_button_labels(button_type, context=None):
    """Generate labels for miscellaneous buttons."""
    labels = []

    if button_type == "more_button":
        labels.append(
            ButtonLabel(
                button_type="more_button",
                context=context or "description",
                title="See more about this playlist",
                aria_label="Expand full playlist description",
            )
        )
    elif button_type == "close_player":
        labels.append(
            ButtonLabel(
                button_type="close_player",
                context="player",
                title="Close music player",
                aria_label="Close the music player",
            )
        )
    elif button_type == "theme_toggle":
        current_theme = context or "light"
        new_theme = "dark" if current_theme == "light" else "light"
        labels.append(
            ButtonLabel(
                button_type="theme_toggle",
                context=current_theme,
                title=f"Switch to {new_theme} theme",
                aria_label=f"Toggle to {new_theme} theme",
            )
        )
    elif button_type == "accept_terms":
        labels.append(
            ButtonLabel(
                button_type="accept_terms",
                context="terms",
                title="Accept terms and privacy policy to continue",
                aria_label="Accept YouTube Terms of Service and Google Privacy Policy",
            )
        )
    elif button_type == "collapse_button":
        # Context format: service_state (e.g., "spotify_collapsed", "main_expanded", "apple_music_expanded")
        if context:
            # Split from the right to handle service names with underscores (like apple_music)
            parts = context.rsplit("_", 1)  # Split only on the last underscore
            if len(parts) == 2:
                service = parts[0]  # This preserves "apple_music" as one piece
                state = parts[1]  # collapsed or expanded
                if service == "main":
                    service_display = "TuneMeld"
                elif service in SERVICE_CONFIGS:
                    service_display = SERVICE_CONFIGS[service]["display_name"]
                else:
                    raise ValueError(f"Invalid service '{service}' in collapse button context '{context}'")
                action = "Expand" if state == "collapsed" else "Collapse"

                labels.append(
                    ButtonLabelType(
                        button_type="collapse_button",
                        context=context,
                        title=f"{action} {service_display} playlist",
                        aria_label=f"{action} {service_display} playlist section",
                    )
                )
    elif button_type == "track_title":
        valid_services = [
            ServiceName.YOUTUBE.value,
            ServiceName.SPOTIFY.value,
            ServiceName.APPLE_MUSIC.value,
            ServiceName.SOUNDCLOUD.value,
        ]
        if context in valid_services:
            service_display = SERVICE_CONFIGS[context]["display_name"]

            labels.append(
                ButtonLabelType(
                    button_type="track_title",
                    context=context,
                    title=f"Play {{trackName}} by {{artistName}} on {service_display}",
                    aria_label=f"Play {{trackName}} by {{artistName}} on {service_display}",
                )
            )

    return labels
