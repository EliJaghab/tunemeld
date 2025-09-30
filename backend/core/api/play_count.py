from core.constants import ServiceName
from core.models.play_counts import AggregatePlayCount
from core.types import PlayCount


def get_track_play_count(isrc: str) -> PlayCount | None:
    play_counts = AggregatePlayCount.objects.filter(isrc=isrc).select_related("service").order_by("-recorded_date")

    latest_date = play_counts.first().recorded_date if play_counts.exists() else None
    if not latest_date:
        return None

    latest_play_counts = play_counts.filter(recorded_date=latest_date)

    spotify_count = None
    youtube_count = None
    total_current = None
    total_weekly_change = None

    for pc in latest_play_counts:
        service_name = pc.service.name

        if service_name == ServiceName.TOTAL.value:
            total_current = pc.current_play_count
            total_weekly_change = pc.weekly_change_percentage
        elif service_name == ServiceName.SPOTIFY.value:
            spotify_count = pc.current_play_count
        elif service_name == ServiceName.YOUTUBE.value:
            youtube_count = pc.current_play_count

    return PlayCount(
        isrc=isrc,
        spotify_current_play_count=spotify_count,
        youtube_current_play_count=youtube_count,
        total_current_play_count=total_current,
        total_weekly_change_percentage=total_weekly_change,
    )
