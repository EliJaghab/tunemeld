import graphene
from core.api.genre_service_api import (
    get_service,
    get_track_rank_by_track_object,
    is_track_seen_on_service,
)
from core.api.track_metadata_api import build_track_query_url
from core.constants import ServiceName
from core.graphql.button_labels import ButtonLabelType, generate_track_button_labels
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
    full_track_name = graphene.String(description="Complete track name without truncation")
    full_artist_name = graphene.String(description="Complete artist name without truncation")
    button_labels = graphene.List(ButtonLabelType, description="Contextual button labels for this track")
    track_detail_url = graphene.String(
        description="Internal URL for this track with genre/rank/player context",
        genre=graphene.String(required=True),
        rank=graphene.String(required=True),
        player=graphene.String(required=True),
    )

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

    def resolve_full_track_name(self, info):
        return self.track_name

    def resolve_full_artist_name(self, info):
        return self.artist_name

    def resolve_button_labels(self, info):
        if hasattr(self, "button_labels"):
            from core.graphql.button_labels import ButtonLabelType

            return [
                ButtonLabelType(
                    buttonType=bl["buttonType"], context=bl["context"], title=bl["title"], ariaLabel=bl["ariaLabel"]
                )
                for bl in self.button_labels
            ]

        genre = info.variable_values.get("genre")
        service = info.variable_values.get("service")
        return generate_track_button_labels(self, genre=genre, service=service)

    def resolve_track_detail_url(self, info, genre, rank, player):
        cache_key = f"track_detail_url_{player}"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)

        return build_track_query_url(genre, rank, self.isrc, player)

    def resolve_tunemeld_rank(self, info, genre, service):
        if hasattr(self, "tunemeld_rank"):
            return self.tunemeld_rank

        return get_track_rank_by_track_object(self, genre, service)

    def resolve_spotify_source(self, info):
        if hasattr(self, "spotify_source") and self.spotify_source:
            return ServiceType(
                name=self.spotify_source["name"],
                display_name=self.spotify_source["display_name"],
                url=self.spotify_source["url"],
                icon_url=self.spotify_source["icon_url"],
            )

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
        if hasattr(self, "apple_music_source") and self.apple_music_source:
            return ServiceType(
                name=self.apple_music_source["name"],
                display_name=self.apple_music_source["display_name"],
                url=self.apple_music_source["url"],
                icon_url=self.apple_music_source["icon_url"],
            )

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
        if hasattr(self, "soundcloud_source") and self.soundcloud_source:
            return ServiceType(
                name=self.soundcloud_source["name"],
                display_name=self.soundcloud_source["display_name"],
                url=self.soundcloud_source["url"],
                icon_url=self.soundcloud_source["icon_url"],
            )

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
        if hasattr(self, "youtube_source") and self.youtube_source:
            return ServiceType(
                name=self.youtube_source["name"],
                display_name=self.youtube_source["display_name"],
                url=self.youtube_source["url"],
                icon_url=self.youtube_source["icon_url"],
            )

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
        if hasattr(self, "seen_on_spotify"):
            return self.seen_on_spotify

        genre_name = info.variable_values["genre"]
        return is_track_seen_on_service(self.isrc, genre_name, ServiceName.SPOTIFY)

    def resolve_seen_on_apple_music(self, info):
        if hasattr(self, "seen_on_apple_music"):
            return self.seen_on_apple_music

        genre_name = info.variable_values["genre"]
        return is_track_seen_on_service(self.isrc, genre_name, ServiceName.APPLE_MUSIC)

    def resolve_seen_on_soundcloud(self, info):
        if hasattr(self, "seen_on_soundcloud"):
            return self.seen_on_soundcloud

        genre_name = info.variable_values["genre"]
        return is_track_seen_on_service(self.isrc, genre_name, ServiceName.SOUNDCLOUD)

    def resolve_soundcloud_rank(self, info):
        if hasattr(self, "soundcloud_rank"):
            return self.soundcloud_rank

        genre_name = info.variable_values.get("genre")
        if not genre_name:
            return None
        return get_track_rank_by_track_object(self, genre_name, ServiceName.SOUNDCLOUD.value)

    def resolve_spotify_rank(self, info):
        if hasattr(self, "spotify_rank"):
            return self.spotify_rank

        genre_name = info.variable_values.get("genre")
        if not genre_name:
            return None
        return get_track_rank_by_track_object(self, genre_name, ServiceName.SPOTIFY.value)

    def resolve_apple_music_rank(self, info):
        if hasattr(self, "apple_music_rank"):
            return self.apple_music_rank

        genre_name = info.variable_values.get("genre")
        if not genre_name:
            return None
        return get_track_rank_by_track_object(self, genre_name, ServiceName.APPLE_MUSIC.value)


class TrackQuery(graphene.ObjectType):
    track_by_isrc = graphene.Field(TrackType, isrc=graphene.String(required=True))

    def resolve_track_by_isrc(self, info, isrc):
        return Track.objects.filter(isrc=isrc).order_by("-id").first()
