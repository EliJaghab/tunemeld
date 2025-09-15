import graphene
from core.graphql.genre import GenreQuery
from core.graphql.playlist import PlaylistQuery
from core.graphql.service import ServiceQuery
from core.graphql.track import TrackQuery


class Query(GenreQuery, PlaylistQuery, TrackQuery, ServiceQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
