import graphene
from core.api.genre_service_api import (
    get_service,
    get_track_rank_by_track_object,
    is_track_seen_on_service,
)
from core.constants import ServiceName
from core.graphql.service import ServiceType
from core.models.genre_service import Service
from core.models.track import Track
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
    soundcloud_rank = graphene.Int(description="Position on SoundCloud playlist for current genre")
    spotify_rank = graphene.Int(description="Position on Spotify playlist for current genre")
    apple_music_rank = graphene.Int(description="Position on Apple Music playlist for current genre")
    spotify_source = graphene.Field(ServiceType, description="Spotify service source with metadata")
    apple_music_source = graphene.Field(ServiceType, description="Apple Music service source with metadata")
    soundcloud_source = graphene.Field(ServiceType, description="SoundCloud service source with metadata")
    youtube_source = graphene.Field(ServiceType, description="YouTube service source with metadata")

    seen_on_spotify = graphene.Boolean(
        description="Whether this track was seen on Spotify playlists for TuneMeld ranking"
    )
    seen_on_apple_music = graphene.Boolean(
        description="Whether this track was seen on Apple Music playlists for TuneMeld ranking"
    )
    seen_on_soundcloud = graphene.Boolean(
        description="Whether this track was seen on SoundCloud playlists for TuneMeld ranking"
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
        return get_track_rank_by_track_object(self, genre, service)

    def resolve_spotify_source(self, info):
        """
        Returns: {name: "spotify", displayName: "Spotify", url: "https://...", iconUrl: "images/..."} or None
        """
        if not self.spotify_url:
            return None
        try:
            service = get_service(ServiceName.SPOTIFY)
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
            service = get_service(ServiceName.APPLE_MUSIC)
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
            service = get_service(ServiceName.SOUNDCLOUD)
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
            service = get_service(ServiceName.YOUTUBE)
            return ServiceType(
                name=ServiceName.YOUTUBE,
                display_name=service.display_name,
                url=self.youtube_url,
                icon_url=service.icon_url,
            )
        except Service.DoesNotExist:
            return None

    def resolve_seen_on_spotify(self, info):
        """Check if this track was seen on Spotify playlists for TuneMeld ranking."""
        genre_name = info.variable_values["genre"]
        return is_track_seen_on_service(self.isrc, genre_name, ServiceName.SPOTIFY)

    def resolve_seen_on_apple_music(self, info):
        """Check if this track was seen on Apple Music playlists for TuneMeld ranking."""
        genre_name = info.variable_values["genre"]
        return is_track_seen_on_service(self.isrc, genre_name, ServiceName.APPLE_MUSIC)

    def resolve_seen_on_soundcloud(self, info):
        """Check if this track was seen on SoundCloud playlists for TuneMeld ranking."""
        genre_name = info.variable_values["genre"]
        return is_track_seen_on_service(self.isrc, genre_name, ServiceName.SOUNDCLOUD)

    def resolve_soundcloud_rank(self, info):
        """Get track position on SoundCloud playlist for current genre"""
        genre_name = info.variable_values.get("genre")
        if not genre_name:
            return None
        return get_track_rank_by_track_object(self, genre_name, ServiceName.SOUNDCLOUD.value)

    def resolve_spotify_rank(self, info):
        """Get track position on Spotify playlist for current genre"""
        genre_name = info.variable_values.get("genre")
        if not genre_name:
            return None
        return get_track_rank_by_track_object(self, genre_name, ServiceName.SPOTIFY.value)

    def resolve_apple_music_rank(self, info):
        """Get track position on Apple Music playlist for current genre"""
        genre_name = info.variable_values.get("genre")
        if not genre_name:
            return None
        return get_track_rank_by_track_object(self, genre_name, ServiceName.APPLE_MUSIC.value)


class TrackQuery(graphene.ObjectType):
    track_by_isrc = graphene.Field(TrackType, isrc=graphene.String(required=True))

    def resolve_track_by_isrc(self, info, isrc):
        return Track.objects.filter(isrc=isrc).order_by("-id").first()
