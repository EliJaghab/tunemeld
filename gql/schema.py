import strawberry

from gql.genre import GenreQuery
from gql.play_count import PlayCountQuery
from gql.playlist import PlaylistQuery
from gql.service import ServiceQuery
from gql.track import TrackQuery


@strawberry.type
class Query(TrackQuery, PlaylistQuery, ServiceQuery, GenreQuery, PlayCountQuery):
    pass


schema = strawberry.Schema(query=Query)
