import graphene
from core.constants import GENRE_CONFIGS, GenreName
from core.graphql.button_labels import ButtonLabelType, generate_genre_button_labels
from core.models.genre_service import GenreModel
from core.settings import DISABLE_CACHE
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from graphene_django import DjangoObjectType


class GenreType(DjangoObjectType):
    class Meta:
        model = GenreModel
        fields = ("id", "name", "display_name", "icon_url")

    button_labels = graphene.List(ButtonLabelType, description="Button labels for this genre")

    def resolve_button_labels(self, info):
        return generate_genre_button_labels(self.name)


class GenreQuery(graphene.ObjectType):
    genres = graphene.List(GenreType)
    default_genre = graphene.String()

    def resolve_genres(self, info):
        cache_key_data = "all_genres"

        cached_result = None if DISABLE_CACHE else redis_cache_get(CachePrefix.GQL_GENRES, cache_key_data)

        if cached_result is not None:
            # Convert cached data back to genre objects with button labels
            genres = []
            for genre_data in cached_result:
                genre = GenreModel(**{k: v for k, v in genre_data.items() if k != "button_labels"})
                genre.button_labels = genre_data.get("button_labels", [])
                genres.append(genre)
            return genres

        genres = GenreModel.objects.all()
        sorted_genres = sorted(genres, key=lambda g: (GENRE_CONFIGS.get(g.name, {}).get("order", 999), g.name))

        # Prepare data for caching with button labels included
        cache_data = []
        for genre in sorted_genres:
            genre_dict = {
                "id": genre.id,
                "name": genre.name,
                "display_name": genre.display_name,
                "icon_url": genre.icon_url,
                "button_labels": [
                    {
                        "buttonType": bl.buttonType,
                        "context": bl.context,
                        "title": bl.title,
                        "ariaLabel": bl.ariaLabel,
                    }
                    for bl in generate_genre_button_labels(genre.name)
                ],
            }
            cache_data.append(genre_dict)

        redis_cache_set(CachePrefix.GQL_GENRES, cache_key_data, cache_data)

        return sorted_genres

    def resolve_default_genre(self, info):
        cache_key_data = "default_genre"

        cached_result = None if DISABLE_CACHE else redis_cache_get(CachePrefix.GQL_GENRES, cache_key_data)

        if cached_result is not None:
            return cached_result

        default_genre = GenreName.POP
        redis_cache_set(CachePrefix.GQL_GENRES, cache_key_data, default_genre)

        return default_genre
