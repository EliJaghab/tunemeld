import graphene
from core.constants import ServiceName
from core.graphql.service import ServiceType
from core.models.genre_service import Service
from core.models.play_counts import AggregatePlayCount, HistoricalTrackPlayCount
from core.models.playlist import Playlist
from core.models.track import Track
from core.utils.utils import format_percentage_change, format_play_count, truncate_to_words
from graphene_django import DjangoObjectType


class TrackType(DjangoObjectType):
    class Meta:
        model = Track
        fields = (
            "id",
            "isrc",
            "album_name",
            "spotify_url",
            "apple_music_url",
            "youtube_url",
            "soundcloud_url",
            "album_cover_url",
            "aggregate_rank",
            "aggregate_score",
            "updated_at",
        )
        convert_choices_to_enum = False

    track_name = graphene.String(description="Track name truncated to 30 characters at word boundaries")
    artist_name = graphene.String(description="Artist name truncated to 30 characters at word boundaries")

    tunemeld_rank = graphene.Int(
        description="Position in the playlist",
        genre=graphene.String(required=True),
        service=graphene.String(required=True),
    )
    spotify_source = graphene.Field(ServiceType, description="Spotify service source with metadata")
    apple_music_source = graphene.Field(ServiceType, description="Apple Music service source with metadata")
    soundcloud_source = graphene.Field(ServiceType, description="SoundCloud service source with metadata")
    youtube_source = graphene.Field(ServiceType, description="YouTube service source with metadata")

    youtube_current_play_count = graphene.BigInt(description="Raw YouTube play count for sorting")
    spotify_current_play_count = graphene.BigInt(description="Raw Spotify play count for sorting")
    soundcloud_current_play_count = graphene.BigInt(description="Raw SoundCloud play count for sorting")
    youtube_current_play_count_abbreviated = graphene.String(
        description="Abbreviated YouTube play count (e.g., '1.56k', '234.5M')"
    )
    spotify_current_play_count_abbreviated = graphene.String(
        description="Abbreviated Spotify play count (e.g., '1.56k', '234.5M')"
    )
    soundcloud_current_play_count_abbreviated = graphene.String(
        description="Abbreviated SoundCloud play count (e.g., '1.56k', '234.5M')"
    )
    youtube_play_count_delta_percentage = graphene.Float(description="YouTube play count % change from yesterday")
    spotify_play_count_delta_percentage = graphene.Float(description="Spotify play count % change from yesterday")
    soundcloud_play_count_delta_percentage = graphene.Float(description="SoundCloud play count % change from yesterday")
    youtube_play_count_delta_percentage_formatted = graphene.String(
        description="YouTube play count % change formatted as 4-char string (e.g., '+.23%')"
    )
    spotify_play_count_delta_percentage_formatted = graphene.String(
        description="Spotify play count % change formatted as 4-char string (e.g., '+.23%')"
    )
    soundcloud_play_count_delta_percentage_formatted = graphene.String(
        description="SoundCloud play count % change formatted as 4-char string (e.g., '+.23%')"
    )

    total_current_play_count = graphene.BigInt(
        description="Combined total of YouTube and Spotify play counts for sorting"
    )
    total_current_play_count_abbreviated = graphene.String(
        description="Abbreviated total play count (e.g., '1.56k', '234.5M')"
    )
    total_weekly_change_percentage = graphene.Float(description="Total play count % change from one week ago")
    total_weekly_change_percentage_formatted = graphene.String(
        description="Total weekly % change formatted as string (e.g., '+23%', '-5.2%')"
    )

    def resolve_track_name(self, info):
        return truncate_to_words(self.track_name, 30) if self.track_name else None

    def resolve_artist_name(self, info):
        return truncate_to_words(self.artist_name, 30) if self.artist_name else None

    def resolve_tunemeld_rank(self, info, genre, service):
        """
        Returns: 1, 2, 3... or None if track not in playlist
        Example: tunemeld_rank(genre="pop", service="spotify") -> 5
        """
        try:
            playlist_entry = (
                Playlist.objects.select_related("service_track")
                .filter(service_track__track=self, genre__name=genre, service__name=service)
                .order_by("position")
                .first()
            )
            return playlist_entry.position if playlist_entry else None
        except Playlist.DoesNotExist:
            return None

    def resolve_spotify_source(self, info):
        """
        Returns: {name: "spotify", displayName: "Spotify", url: "https://...", iconUrl: "images/..."} or None
        """
        if not self.spotify_url:
            return None
        try:
            service = Service.objects.get(name=ServiceName.SPOTIFY)
            return ServiceType(
                name=ServiceName.SPOTIFY,
                display_name=service.display_name,
                url=self.spotify_url,
                icon_url=service.icon_url,
            )
        except Service.DoesNotExist:
            return None

    def resolve_apple_music_source(self, info):
        if not self.apple_music_url:
            return None
        try:
            service = Service.objects.get(name=ServiceName.APPLE_MUSIC)
            return ServiceType(
                name=ServiceName.APPLE_MUSIC,
                display_name=service.display_name,
                url=self.apple_music_url,
                icon_url=service.icon_url,
            )
        except Service.DoesNotExist:
            return None

    def resolve_soundcloud_source(self, info):
        if not self.soundcloud_url:
            return None
        try:
            service = Service.objects.get(name=ServiceName.SOUNDCLOUD)
            return ServiceType(
                name=ServiceName.SOUNDCLOUD,
                display_name=service.display_name,
                url=self.soundcloud_url,
                icon_url=service.icon_url,
            )
        except Service.DoesNotExist:
            return None

    def resolve_youtube_source(self, info):
        if not self.youtube_url:
            return None
        try:
            service = Service.objects.get(name=ServiceName.YOUTUBE)
            return ServiceType(
                name=ServiceName.YOUTUBE,
                display_name=service.display_name,
                url=self.youtube_url,
                icon_url=service.icon_url,
            )
        except Service.DoesNotExist:
            return None

    def resolve_youtube_current_play_count(self, info):
        # Always prefer pre-populated data from cache (including explicit None for Saturdays)
        if hasattr(self, "_youtube_current_play_count"):
            return self._youtube_current_play_count

        # Fallback to database only when cache is completely empty
        # This handles edge cases where cache warming failed
        try:
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            latest = (
                HistoricalTrackPlayCount.objects.filter(isrc=self.isrc, service=youtube_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.current_play_count if latest else None
        except (Service.DoesNotExist, HistoricalTrackPlayCount.DoesNotExist):
            return None

    def resolve_spotify_current_play_count(self, info):
        if hasattr(self, "_spotify_current_play_count"):
            return self._spotify_current_play_count

        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            latest = (
                HistoricalTrackPlayCount.objects.filter(isrc=self.isrc, service=spotify_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.current_play_count if latest else None
        except (Service.DoesNotExist, HistoricalTrackPlayCount.DoesNotExist):
            return None

    def resolve_youtube_current_play_count_abbreviated(self, info):
        # Always prefer pre-populated data from cache (including explicit None for Saturdays)
        if hasattr(self, "_youtube_current_play_count"):
            raw_count = self._youtube_current_play_count
            return format_play_count(raw_count)

        # Fallback to database only when cache is completely empty
        try:
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            latest = (
                HistoricalTrackPlayCount.objects.filter(isrc=self.isrc, service=youtube_service)
                .order_by("-recorded_date")
                .first()
            )
            raw_count = latest.current_play_count if latest else None
            return format_play_count(raw_count)
        except (Service.DoesNotExist, HistoricalTrackPlayCount.DoesNotExist):
            return format_play_count(None)

    def resolve_spotify_current_play_count_abbreviated(self, info):
        if hasattr(self, "_spotify_current_play_count"):
            raw_count = self._spotify_current_play_count
            return format_play_count(raw_count)

        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            latest = (
                HistoricalTrackPlayCount.objects.filter(isrc=self.isrc, service=spotify_service)
                .order_by("-recorded_date")
                .first()
            )
            raw_count = latest.current_play_count if latest else None
            return format_play_count(raw_count)
        except (Service.DoesNotExist, HistoricalTrackPlayCount.DoesNotExist):
            return format_play_count(None)

    def resolve_youtube_play_count_delta_percentage(self, info):
        if hasattr(self, "_youtube_play_count_delta_percentage"):
            return self._youtube_play_count_delta_percentage

        try:
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=youtube_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.weekly_change_percentage if latest else None
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return None

    def resolve_spotify_play_count_delta_percentage(self, info):
        if hasattr(self, "_spotify_play_count_delta_percentage"):
            return self._spotify_play_count_delta_percentage

        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=spotify_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.weekly_change_percentage if latest else None
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return None

    def resolve_soundcloud_current_play_count(self, info):
        if hasattr(self, "_soundcloud_current_play_count"):
            return self._soundcloud_current_play_count

        try:
            soundcloud_service = Service.objects.get(name=ServiceName.SOUNDCLOUD)
            latest = (
                HistoricalTrackPlayCount.objects.filter(isrc=self.isrc, service=soundcloud_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.current_play_count if latest else None
        except (Service.DoesNotExist, HistoricalTrackPlayCount.DoesNotExist):
            return None

    def resolve_soundcloud_current_play_count_abbreviated(self, info):
        if hasattr(self, "_soundcloud_current_play_count"):
            raw_count = self._soundcloud_current_play_count
            return format_play_count(raw_count)

        try:
            soundcloud_service = Service.objects.get(name=ServiceName.SOUNDCLOUD)
            latest = (
                HistoricalTrackPlayCount.objects.filter(isrc=self.isrc, service=soundcloud_service)
                .order_by("-recorded_date")
                .first()
            )
            raw_count = latest.current_play_count if latest else None
            return format_play_count(raw_count)
        except (Service.DoesNotExist, HistoricalTrackPlayCount.DoesNotExist):
            return format_play_count(None)

    def resolve_soundcloud_play_count_delta_percentage(self, info):
        if hasattr(self, "_soundcloud_play_count_delta_percentage"):
            return self._soundcloud_play_count_delta_percentage

        try:
            soundcloud_service = Service.objects.get(name=ServiceName.SOUNDCLOUD)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=soundcloud_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.weekly_change_percentage if latest else None
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return None

    def resolve_soundcloud_play_count_delta_percentage_formatted(self, info):
        if hasattr(self, "_soundcloud_play_count_delta_percentage"):
            return format_percentage_change(self._soundcloud_play_count_delta_percentage)

        try:
            soundcloud_service = Service.objects.get(name=ServiceName.SOUNDCLOUD)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=soundcloud_service)
                .order_by("-recorded_date")
                .first()
            )
            percentage = latest.weekly_change_percentage if latest else None
            return format_percentage_change(percentage)
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return format_percentage_change(None)

    def resolve_youtube_play_count_delta_percentage_formatted(self, info):
        if hasattr(self, "_youtube_play_count_delta_percentage"):
            return format_percentage_change(self._youtube_play_count_delta_percentage)

        try:
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=youtube_service)
                .order_by("-recorded_date")
                .first()
            )
            percentage = latest.weekly_change_percentage if latest else None
            return format_percentage_change(percentage)
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return format_percentage_change(None)

    def resolve_spotify_play_count_delta_percentage_formatted(self, info):
        if hasattr(self, "_spotify_play_count_delta_percentage"):
            return format_percentage_change(self._spotify_play_count_delta_percentage)

        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=spotify_service)
                .order_by("-recorded_date")
                .first()
            )
            percentage = latest.weekly_change_percentage if latest else None
            return format_percentage_change(percentage)
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return format_percentage_change(None)

    def resolve_total_current_play_count(self, info):
        """Get combined YouTube, Spotify, and SoundCloud play counts from aggregate data."""
        try:
            total_service = Service.objects.get(name=ServiceName.TOTAL)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=total_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.current_play_count if latest else 0
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            # Fallback to calculated total if aggregate data not available
            youtube_count = self.resolve_youtube_current_play_count(info) or 0
            spotify_count = self.resolve_spotify_current_play_count(info) or 0
            soundcloud_count = self.resolve_soundcloud_current_play_count(info) or 0
            return youtube_count + spotify_count + soundcloud_count

    def resolve_total_current_play_count_abbreviated(self, info):
        """Get formatted combined play count string."""
        try:
            total_service = Service.objects.get(name=ServiceName.TOTAL)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=total_service)
                .order_by("-recorded_date")
                .first()
            )
            total_count = latest.current_play_count if latest else 0
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            # Fallback to calculated total if aggregate data not available
            youtube_count = getattr(self, "_youtube_current_play_count", None) or 0
            spotify_count = getattr(self, "_spotify_current_play_count", None) or 0
            soundcloud_count = getattr(self, "_soundcloud_current_play_count", None) or 0
            total_count = youtube_count + spotify_count + soundcloud_count
        return format_play_count(total_count)

    def resolve_total_weekly_change_percentage(self, info):
        """Get total weekly change percentage from aggregate data."""
        try:
            total_service = Service.objects.get(name=ServiceName.TOTAL)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=total_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.weekly_change_percentage if latest else None
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            return None

    def resolve_total_weekly_change_percentage_formatted(self, info):
        """Get formatted weekly change percentage string."""
        try:
            total_service = Service.objects.get(name=ServiceName.TOTAL)
            latest = (
                AggregatePlayCount.objects.filter(isrc=self.isrc, service=total_service)
                .order_by("-recorded_date")
                .first()
            )
            percentage = latest.weekly_change_percentage if latest else None
        except (Service.DoesNotExist, AggregatePlayCount.DoesNotExist):
            percentage = None
        return format_percentage_change(percentage)


class TrackQuery(graphene.ObjectType):
    track_by_isrc = graphene.Field(TrackType, isrc=graphene.String(required=True))

    def resolve_track_by_isrc(self, info, isrc):
        try:
            return Track.objects.get(isrc=isrc)
        except Track.DoesNotExist:
            return None
