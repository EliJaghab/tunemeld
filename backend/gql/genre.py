from typing import Any, cast

import strawberry
from core.constants import GENRE_CONFIGS, GenreName, GraphQLCacheKey
from core.models.genre_service import GenreModel
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import Genre

from backend.gql.button_labels import ButtonLabelType, generate_genre_button_labels


@strawberry.type
class GenreType:
    id: int
    name: str
    display_name: str
    icon_url: str | None

    @strawberry.field(description="Button labels for this genre")
    def button_labels(self) -> list[ButtonLabelType]:
        return generate_genre_button_labels(self.name)

    @classmethod
    def from_django_model(cls, genre_model: GenreModel):
        return cls(
            id=genre_model.id,
            name=genre_model.name,
            display_name=genre_model.display_name,
            icon_url=genre_model.icon_url,
        )


@strawberry.type
class GenreQuery:
    @strawberry.field
    def genres(self) -> list[GenreType]:
        cached_result = redis_cache_get(CachePrefix.GQL_GENRES, GraphQLCacheKey.ALL_GENRES)

        if cached_result is not None:
            # Convert cached data back to genre objects with button labels
            genres = []
            genre_data_list = cast("list[dict[str, Any]]", cached_result)
            for genre_data in genre_data_list:
                genre = GenreModel(**{k: v for k, v in genre_data.items() if k != "button_labels"})
                genre.button_labels = genre_data.get("button_labels", [])
                genres.append(GenreType.from_django_model(genre))
            return genres

        genres = list(GenreModel.objects.all())
        sorted_genres = sorted(genres, key=lambda g: (GENRE_CONFIGS.get(g.name, {}).get("order", 999), g.name))

        cache_data = []
        for genre in sorted_genres:
            domain_genre = Genre.from_django_model(genre)
            button_labels = generate_genre_button_labels(genre.name)
            genre_dict = domain_genre.to_dict_with_button_labels(button_labels)
            cache_data.append(genre_dict)

        redis_cache_set(CachePrefix.GQL_GENRES, GraphQLCacheKey.ALL_GENRES, cache_data)

        return [GenreType.from_django_model(genre) for genre in sorted_genres]

    @strawberry.field
    def default_genre(self) -> str:
        return GenreName.POP
