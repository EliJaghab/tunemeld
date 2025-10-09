from datetime import datetime

import strawberry
from core.api.play_count import get_track_play_count
from core.constants import GraphQLCacheKey
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set


@strawberry.type
class TrackPlayCountType:
    """Complete play count data for a track with service-specific columns."""

    isrc: str

    spotify_current_play_count: float | None = None
    spotify_weekly_change_percentage: float | None = None
    spotify_updated_at: datetime | None = None
    spotify_current_play_count_abbreviated: str | None = None
    spotify_weekly_change_percentage_formatted: str | None = None

    apple_music_current_play_count: float | None = None
    apple_music_weekly_change_percentage: float | None = None
    apple_music_updated_at: datetime | None = None
    apple_music_current_play_count_abbreviated: str | None = None
    apple_music_weekly_change_percentage_formatted: str | None = None

    youtube_current_play_count: float | None = None
    youtube_weekly_change_percentage: float | None = None
    youtube_updated_at: datetime | None = None
    youtube_current_play_count_abbreviated: str | None = None
    youtube_weekly_change_percentage_formatted: str | None = None

    soundcloud_current_play_count: float | None = None
    soundcloud_weekly_change_percentage: float | None = None
    soundcloud_updated_at: datetime | None = None
    soundcloud_current_play_count_abbreviated: str | None = None
    soundcloud_weekly_change_percentage_formatted: str | None = None

    total_current_play_count: float | None = None
    total_weekly_change_percentage: float | None = None
    total_current_play_count_abbreviated: str | None = None
    total_weekly_change_percentage_formatted: str | None = None


@strawberry.type
class PlayCountQuery:
    @strawberry.field(description="Get play count data for a specific track by ISRC")
    def track_play_count(self, isrc: str) -> TrackPlayCountType | None:
        """Get play count data for a single track."""
        return PlayCountQuery._get_track_play_count(isrc)

    @strawberry.field(description="Get play count data for multiple tracks by ISRCs")
    def tracks_play_counts(self, isrcs: list[str]) -> list[TrackPlayCountType]:
        """Get play count data for multiple tracks."""
        results = []
        for isrc in isrcs:
            play_count = PlayCountQuery._get_track_play_count(isrc)
            if play_count is not None:
                results.append(play_count)
        return results

    @staticmethod
    def _get_track_play_count(isrc: str) -> TrackPlayCountType | None:
        """Internal method to get play count data for a track."""
        cache_key = GraphQLCacheKey.track_play_count(isrc)

        cached_data = redis_cache_get(CachePrefix.GQL_PLAY_COUNT, cache_key)

        if cached_data:
            return TrackPlayCountType(**cached_data)

        play_count_data = get_track_play_count(isrc)
        if not play_count_data:
            return None

        result_data = play_count_data.to_dict()

        redis_cache_set(CachePrefix.GQL_PLAY_COUNT, cache_key, result_data)

        return TrackPlayCountType(**result_data)
