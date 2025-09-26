import graphene
from core.api.genre_service_api import get_all_genres
from core.constants import GENRE_CONFIGS, GenreName
from core.models import Genre
from graphene_django import DjangoObjectType


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre
        fields = ("id", "name", "display_name", "icon_url")


class GenreQuery(graphene.ObjectType):
    genres = graphene.List(GenreType)
    default_genre = graphene.String()

    def resolve_genres(self, info):
        genres = get_all_genres()
        return sorted(genres, key=lambda g: (GENRE_CONFIGS.get(g.name, {}).get("order", 999), g.name))

    def resolve_default_genre(self, info):
        return GenreName.POP
