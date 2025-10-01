import graphene
from core.api.play_count import get_track_play_count
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set


class TrackPlayCountType(graphene.ObjectType):
    """Complete play count data for a track with service-specific columns."""

    isrc = graphene.String(required=True)

    spotify_current_play_count = graphene.Int()
    spotify_weekly_change_percentage = graphene.Float()
    spotify_updated_at = graphene.DateTime()
    spotify_current_play_count_abbreviated = graphene.String()
    spotify_weekly_change_percentage_formatted = graphene.String()

    apple_music_current_play_count = graphene.Int()
    apple_music_weekly_change_percentage = graphene.Float()
    apple_music_updated_at = graphene.DateTime()
    apple_music_current_play_count_abbreviated = graphene.String()
    apple_music_weekly_change_percentage_formatted = graphene.String()

    youtube_current_play_count = graphene.Int()
    youtube_weekly_change_percentage = graphene.Float()
    youtube_updated_at = graphene.DateTime()
    youtube_current_play_count_abbreviated = graphene.String()
    youtube_weekly_change_percentage_formatted = graphene.String()

    soundcloud_current_play_count = graphene.Int()
    soundcloud_weekly_change_percentage = graphene.Float()
    soundcloud_updated_at = graphene.DateTime()
    soundcloud_current_play_count_abbreviated = graphene.String()
    soundcloud_weekly_change_percentage_formatted = graphene.String()

    total_current_play_count = graphene.Int()
    total_weekly_change_percentage = graphene.Float()
    total_current_play_count_abbreviated = graphene.String()
    total_weekly_change_percentage_formatted = graphene.String()


class PlayCountQuery(graphene.ObjectType):
    track_play_count = graphene.Field(
        TrackPlayCountType,
        isrc=graphene.String(required=True),
        description="Get play count data for a specific track by ISRC",
    )

    tracks_play_counts = graphene.List(
        TrackPlayCountType,
        isrcs=graphene.List(graphene.String, required=True),
        description="Get play count data for multiple tracks by ISRCs",
    )

    @staticmethod
    def resolve_track_play_count(root, info, isrc):
        """Get play count data for a single track."""
        return PlayCountQuery._get_track_play_count(isrc, info)

    @staticmethod
    def resolve_tracks_play_counts(root, info, isrcs):
        """Get play count data for multiple tracks."""
        return [PlayCountQuery._get_track_play_count(isrc, info) for isrc in isrcs]

    @staticmethod
    def _get_track_play_count(isrc, info=None):
        """Internal method to get play count data for a track."""
        cache_key = f"track_play_count:{isrc}"

        cached_data = redis_cache_get(CachePrefix.GQL_PLAY_COUNT, cache_key)

        if cached_data:
            return TrackPlayCountType(**cached_data)

        play_count_data = get_track_play_count(isrc)
        if not play_count_data:
            return None

        result_data = play_count_data.to_dict()

        redis_cache_set(CachePrefix.GQL_PLAY_COUNT, cache_key, result_data)

        return TrackPlayCountType(**result_data)
