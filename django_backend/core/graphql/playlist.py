import graphene
from core.models.b_raw_playlist import RawPlaylistData
from graphene_django import DjangoObjectType

from playlist_etl.constants import ServiceName


class PlaylistType(DjangoObjectType):
    class Meta:
        model = RawPlaylistData
        fields = (
            "id",
            "playlist_name",
            "playlist_cover_url",
            "playlist_cover_description_text",
            "playlist_url",
            "created_at",
        )

    genre_name = graphene.String()
    service_name = graphene.String()

    def resolve_genre_name(self, info):
        return self.genre.name

    def resolve_service_name(self, info):
        return self.service.name


class PlaylistQuery(graphene.ObjectType):
    playlists_by_genre = graphene.List(PlaylistType, genre=graphene.String(required=True))
    service_order = graphene.List(graphene.String)

    def resolve_playlists_by_genre(self, info, genre):
        return (
            RawPlaylistData.objects.select_related("genre", "service")
            .filter(genre__name=genre)
            .order_by("service__name")
        )

    def resolve_service_order(self, info):
        return [ServiceName.SOUNDCLOUD, ServiceName.APPLE_MUSIC, ServiceName.SPOTIFY]
