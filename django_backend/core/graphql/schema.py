import graphene
from core.graphql.genre import GenreQuery
from core.graphql.playlist import PlaylistQuery


class Query(GenreQuery, PlaylistQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
