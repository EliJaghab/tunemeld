import graphene
from core.constants import ServiceName
from core.graphql.service import ServiceType
from core.models.genre_service import Service
from core.models.playlist import Playlist
from core.models.track import Track
from core.models.view_counts import HistoricalTrackViewCount
from core.utils.utils import truncate_to_words
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

    youtube_current_view_count = graphene.BigInt(description="Current YouTube view count")
    spotify_current_view_count = graphene.BigInt(description="Current Spotify view count")
    youtube_view_count_delta_percentage = graphene.Float(description="YouTube view count % change from yesterday")
    spotify_view_count_delta_percentage = graphene.Float(description="Spotify view count % change from yesterday")

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

    def resolve_youtube_current_view_count(self, info):
        # Always prefer pre-populated data from cache (including explicit None for Saturdays)
        if hasattr(self, "_youtube_current_view_count"):
            return self._youtube_current_view_count

        # Fallback to database only when cache is completely empty
        # This handles edge cases where cache warming failed
        try:
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            latest = (
                HistoricalTrackViewCount.objects.filter(isrc=self.isrc, service=youtube_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.current_view_count if latest else None
        except (Service.DoesNotExist, HistoricalTrackViewCount.DoesNotExist):
            return None

    def resolve_spotify_current_view_count(self, info):
        if hasattr(self, "_spotify_current_view_count"):
            return self._spotify_current_view_count

        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            latest = (
                HistoricalTrackViewCount.objects.filter(isrc=self.isrc, service=spotify_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.current_view_count if latest else None
        except (Service.DoesNotExist, HistoricalTrackViewCount.DoesNotExist):
            return None

    def resolve_youtube_view_count_delta_percentage(self, info):
        if hasattr(self, "_youtube_view_count_delta_percentage"):
            return self._youtube_view_count_delta_percentage

        try:
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            latest = (
                HistoricalTrackViewCount.objects.filter(isrc=self.isrc, service=youtube_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.daily_change_percentage if latest else None
        except (Service.DoesNotExist, HistoricalTrackViewCount.DoesNotExist):
            return None

    def resolve_spotify_view_count_delta_percentage(self, info):
        if hasattr(self, "_spotify_view_count_delta_percentage"):
            return self._spotify_view_count_delta_percentage

        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            latest = (
                HistoricalTrackViewCount.objects.filter(isrc=self.isrc, service=spotify_service)
                .order_by("-recorded_date")
                .first()
            )
            return latest.daily_change_percentage if latest else None
        except (Service.DoesNotExist, HistoricalTrackViewCount.DoesNotExist):
            return None


class TrackQuery(graphene.ObjectType):
    track_by_isrc = graphene.Field(TrackType, isrc=graphene.String(required=True))

    def resolve_track_by_isrc(self, info, isrc):
        try:
            return Track.objects.get(isrc=isrc)
        except Track.DoesNotExist:
            return None
