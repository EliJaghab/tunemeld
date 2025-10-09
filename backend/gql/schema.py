import strawberry
from strawberry.schema.config import StrawberryConfig

from backend.gql.genre import GenreQuery
from backend.gql.play_count import PlayCountQuery
from backend.gql.playlist import PlaylistQuery
from backend.gql.service import ServiceQuery
from backend.gql.track import TrackQuery


@strawberry.type
class Query(TrackQuery, PlaylistQuery, ServiceQuery, GenreQuery, PlayCountQuery):
    pass


schema = strawberry.Schema(query=Query, config=StrawberryConfig(auto_camel_case=True))
