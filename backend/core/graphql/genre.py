import graphene
from core.constants import GENRE_ORDER, GenreName
from core.models import Genre
from graphene_django import DjangoObjectType


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre
        fields = ("id", "name", "display_name")


class GenreQuery(graphene.ObjectType):
    genres = graphene.List(GenreType)
    default_genre = graphene.String()

    def resolve_genres(self, info):
        genres = Genre.objects.all()
        return sorted(genres, key=lambda g: (GENRE_ORDER.index(g.name) if g.name in GENRE_ORDER else 999, g.name))

    def resolve_default_genre(self, info):
        return GenreName.POP
