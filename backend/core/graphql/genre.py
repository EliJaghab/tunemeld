import graphene
from core.api.genre_service_api import get_all_genres
from core.constants import GENRE_CONFIGS, GenreName
from core.graphql.button_labels import ButtonLabelType, generate_genre_button_labels
from core.models import Genre
from graphene_django import DjangoObjectType


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre
        fields = ("id", "name", "display_name", "icon_url")

    button_labels = graphene.List(ButtonLabelType, description="Button labels for this genre")

    def resolve_button_labels(self, info):
        return generate_genre_button_labels(self.name)


class GenreQuery(graphene.ObjectType):
    genres = graphene.List(GenreType)
    default_genre = graphene.String()

    def resolve_genres(self, info):
        genres = get_all_genres()
        return sorted(genres, key=lambda g: (GENRE_CONFIGS.get(g.name, {}).get("order", 999), g.name))

    def resolve_default_genre(self, info):
        return GenreName.POP
