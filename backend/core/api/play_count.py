from dataclasses import dataclass
from datetime import datetime

from core.constants import ServiceName
from core.models.play_counts import AggregatePlayCount


@dataclass
class ServicePlayCountData:
    """Play count data for a specific service."""

    current_play_count: int | None
    weekly_change_percentage: float | None
    updated_at: datetime | None


@dataclass
class TrackPlayCountData:
    """Complete play count data for a track with service-specific columns."""

    isrc: str
    spotify: ServicePlayCountData
    apple_music: ServicePlayCountData
    youtube: ServicePlayCountData
    soundcloud: ServicePlayCountData
    total_current_play_count: int | None
    total_weekly_change_percentage: float | None


def get_track_play_count(isrc: str) -> TrackPlayCountData | None:
    play_counts = AggregatePlayCount.objects.filter(isrc=isrc).select_related("service").order_by("-recorded_date")

    latest_date = play_counts.first().recorded_date if play_counts.exists() else None
    if not latest_date:
        return None

    latest_play_counts = play_counts.filter(recorded_date=latest_date)

    service_data = {
        ServiceName.SPOTIFY.value: ServicePlayCountData(None, None, None),
        ServiceName.APPLE_MUSIC.value: ServicePlayCountData(None, None, None),
        ServiceName.YOUTUBE.value: ServicePlayCountData(None, None, None),
        ServiceName.SOUNDCLOUD.value: ServicePlayCountData(None, None, None),
    }

    total_current = None
    total_weekly_change = None

    for pc in latest_play_counts:
        service_name = pc.service.name

        if service_name == ServiceName.TOTAL.value:
            total_current = pc.current_play_count
            total_weekly_change = pc.weekly_change_percentage
        elif service_name in service_data:
            service_data[service_name] = ServicePlayCountData(
                current_play_count=pc.current_play_count,
                weekly_change_percentage=pc.weekly_change_percentage,
                updated_at=pc.updated_at,
            )

    return TrackPlayCountData(
        isrc=isrc,
        spotify=service_data[ServiceName.SPOTIFY.value],
        apple_music=service_data[ServiceName.APPLE_MUSIC.value],
        youtube=service_data[ServiceName.YOUTUBE.value],
        soundcloud=service_data[ServiceName.SOUNDCLOUD.value],
        total_current_play_count=total_current,
        total_weekly_change_percentage=total_weekly_change,
    )
