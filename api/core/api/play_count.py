from core.constants import ServiceName
from core.models.play_counts import AggregatePlayCountModel
from domain_types.types import ServicePlayCount, TrackPlayCountData


def get_track_play_count(isrc: str) -> TrackPlayCountData | None:
    play_counts = AggregatePlayCountModel.objects.filter(isrc=isrc).select_related("service").order_by("-recorded_date")

    latest_date = play_counts.first().recorded_date if play_counts.exists() else None
    if not latest_date:
        return None

    latest_play_counts = play_counts.filter(recorded_date=latest_date)

    spotify_data = ServicePlayCount(None, None, None)
    apple_music_data = ServicePlayCount(None, None, None)
    youtube_data = ServicePlayCount(None, None, None)
    soundcloud_data = ServicePlayCount(None, None, None)
    total_current = None
    total_weekly_change = None

    for pc in latest_play_counts:
        service_name = pc.service.name

        if service_name == ServiceName.TOTAL.value:
            total_current = pc.current_play_count
            total_weekly_change = pc.weekly_change_percentage
        elif service_name == ServiceName.SPOTIFY.value:
            spotify_data = ServicePlayCount(pc.current_play_count, pc.weekly_change_percentage, pc.updated_at)
        elif service_name == ServiceName.YOUTUBE.value:
            youtube_data = ServicePlayCount(pc.current_play_count, pc.weekly_change_percentage, pc.updated_at)
        elif service_name == ServiceName.APPLE_MUSIC.value:
            apple_music_data = ServicePlayCount(pc.current_play_count, pc.weekly_change_percentage, pc.updated_at)
        elif service_name == ServiceName.SOUNDCLOUD.value:
            soundcloud_data = ServicePlayCount(pc.current_play_count, pc.weekly_change_percentage, pc.updated_at)

    return TrackPlayCountData(
        isrc=isrc,
        spotify=spotify_data,
        apple_music=apple_music_data,
        youtube=youtube_data,
        soundcloud=soundcloud_data,
        total_current_play_count=total_current,
        total_weekly_change_percentage=total_weekly_change,
    )
