import graphene
from core.models import Genre
from core.utils.constants import GenreName
from graphene_django import DjangoObjectType


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre
        fields = ("id", "name", "display_name")


class GenreQuery(graphene.ObjectType):
    genres = graphene.List(GenreType)
    default_genre = graphene.String()

    def resolve_genres(self, info):
        return Genre.objects.all().order_by("name")

    def resolve_default_genre(self, info):
        return GenreName.POP
