import graphene
from core.api.play_count import get_track_play_count
from core.utils.local_cache import CachePrefix, local_cache_get, local_cache_set
from core.utils.utils import format_percentage_change, format_play_count


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
        return PlayCountQuery._get_track_play_count(isrc)

    @staticmethod
    def resolve_tracks_play_counts(root, info, isrcs):
        """Get play count data for multiple tracks."""
        return [PlayCountQuery._get_track_play_count(isrc) for isrc in isrcs]

    @staticmethod
    def _get_track_play_count(isrc):
        """Internal method to get play count data for a track."""
        cache_key = f"track_play_count:{isrc}"

        cached_data = local_cache_get(CachePrefix.GQL_PLAY_COUNT, cache_key)
        if cached_data:
            return cached_data

        play_count_data = get_track_play_count(isrc)
        if not play_count_data:
            return None

        result = TrackPlayCountType(
            isrc=play_count_data.isrc,
            spotify_current_play_count=play_count_data.spotify.current_play_count,
            spotify_weekly_change_percentage=play_count_data.spotify.weekly_change_percentage,
            spotify_updated_at=play_count_data.spotify.updated_at,
            spotify_current_play_count_abbreviated=format_play_count(play_count_data.spotify.current_play_count),
            spotify_weekly_change_percentage_formatted=format_percentage_change(
                play_count_data.spotify.weekly_change_percentage
            ),
            apple_music_current_play_count=play_count_data.apple_music.current_play_count,
            apple_music_weekly_change_percentage=play_count_data.apple_music.weekly_change_percentage,
            apple_music_updated_at=play_count_data.apple_music.updated_at,
            apple_music_current_play_count_abbreviated=format_play_count(
                play_count_data.apple_music.current_play_count
            ),
            apple_music_weekly_change_percentage_formatted=format_percentage_change(
                play_count_data.apple_music.weekly_change_percentage
            ),
            youtube_current_play_count=play_count_data.youtube.current_play_count,
            youtube_weekly_change_percentage=play_count_data.youtube.weekly_change_percentage,
            youtube_updated_at=play_count_data.youtube.updated_at,
            youtube_current_play_count_abbreviated=format_play_count(play_count_data.youtube.current_play_count),
            youtube_weekly_change_percentage_formatted=format_percentage_change(
                play_count_data.youtube.weekly_change_percentage
            ),
            soundcloud_current_play_count=play_count_data.soundcloud.current_play_count,
            soundcloud_weekly_change_percentage=play_count_data.soundcloud.weekly_change_percentage,
            soundcloud_updated_at=play_count_data.soundcloud.updated_at,
            soundcloud_current_play_count_abbreviated=format_play_count(play_count_data.soundcloud.current_play_count),
            soundcloud_weekly_change_percentage_formatted=format_percentage_change(
                play_count_data.soundcloud.weekly_change_percentage
            ),
            total_current_play_count=play_count_data.total_current_play_count,
            total_weekly_change_percentage=play_count_data.total_weekly_change_percentage,
            total_current_play_count_abbreviated=format_play_count(play_count_data.total_current_play_count),
            total_weekly_change_percentage_formatted=format_percentage_change(
                play_count_data.total_weekly_change_percentage
            ),
        )

        local_cache_set(CachePrefix.GQL_PLAY_COUNT, cache_key, result)

        return result
