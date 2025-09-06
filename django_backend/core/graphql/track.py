import graphene
from core.graphql.service import ServiceType
from core.models.b_genre_service import Service
from core.models.e_playlist import Playlist
from core.models.d_track import Track
from graphene_django import DjangoObjectType

from playlist_etl.constants import ServiceName


class TrackType(DjangoObjectType):
    class Meta:
        model = Track
        fields = (
            "isrc",
            "track_name",
            "artist_name",
            "album_name",
            "spotify_url",
            "apple_music_url",
            "youtube_url",
            "soundcloud_url",
            "album_cover_url",
            "aggregate_rank",
            "aggregate_score",
        )
        convert_choices_to_enum = False

    rank = graphene.Int(
        description="Position in the playlist",
        genre=graphene.String(required=True),
        service=graphene.String(required=True),
    )
    service_url = graphene.String(
        description="Service-specific URL", genre=graphene.String(required=True), service=graphene.String(required=True)
    )
    service_name = graphene.String(
        description="Service name for the playlist context",
        genre=graphene.String(required=True),
        service=graphene.String(required=True),
    )
    genre_name = graphene.String(
        description="Genre name for the playlist context",
        genre=graphene.String(required=True),
        service=graphene.String(required=True),
    )
    spotify_source = graphene.Field(ServiceType, description="Spotify service source with metadata")
    apple_music_source = graphene.Field(ServiceType, description="Apple Music service source with metadata")
    soundcloud_source = graphene.Field(ServiceType, description="SoundCloud service source with metadata")
    youtube_source = graphene.Field(ServiceType, description="YouTube service source with metadata")

    view_count_data_json = graphene.JSONString(description="View count data")

    def resolve_rank(self, info, genre, service):
        """
        Returns: 1, 2, 3... or None if track not in playlist
        Example: rank(genre="pop", service="spotify") -> 5
        """
        try:
            playlist_entry = Playlist.objects.select_related("service_track").get(
                service_track__track=self, genre__name=genre, service__name=service
            )
            return playlist_entry.position
        except Playlist.DoesNotExist:
            return None

    def resolve_service_url(self, info, genre, service):
        """
        Returns: "https://open.spotify.com/track/xyz" or None
        Example: serviceUrl(genre="pop", service="spotify") -> "https://open.spotify.com/track/2yWlGE..."
        """
        try:
            playlist_entry = Playlist.objects.select_related("service_track").get(
                service_track__track=self, genre__name=genre, service__name=service
            )
            return playlist_entry.service_track.service_url
        except Playlist.DoesNotExist:
            return None

    def resolve_service_name(self, info, genre, service):
        return service

    def resolve_genre_name(self, info, genre, service):
        return genre

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


class TrackQuery(graphene.ObjectType):
    track_by_isrc = graphene.Field(TrackType, isrc=graphene.String(required=True))

    def resolve_track_by_isrc(self, info, isrc):
        try:
            return Track.objects.get(isrc=isrc)
        except Track.DoesNotExist:
            return None
