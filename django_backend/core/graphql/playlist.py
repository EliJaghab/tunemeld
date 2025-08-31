import graphene
from core.graphql.track import TrackType
from core.models.c_playlist import Playlist

from playlist_etl.constants import ServiceName


class PlaylistType(graphene.ObjectType):
    """GraphQL type for playlists with tracks."""

    genre_name = graphene.String(required=True)
    service_name = graphene.String(required=True)
    tracks = graphene.List(TrackType, required=True)


class PlaylistQuery(graphene.ObjectType):
    service_order = graphene.List(graphene.String)
    playlist = graphene.Field(
        PlaylistType, genre=graphene.String(required=True), service=graphene.String(required=True)
    )

    def resolve_service_order(self, info):
        """Used to order the header art."""
        return [ServiceName.SOUNDCLOUD, ServiceName.APPLE_MUSIC, ServiceName.SPOTIFY]

    def resolve_playlist(self, info, genre, service):
        """Get playlist data for any service (including Aggregate) and genre."""
        playlists = (
            Playlist.objects.select_related("service_track", "service_track__track")
            .filter(genre__name=genre, service__name=service)
            .order_by("position")
        )

        tracks = [
            playlist_entry.service_track.track
            for playlist_entry in playlists
            if playlist_entry.service_track and playlist_entry.service_track.track
        ]

        return PlaylistType(genre_name=genre, service_name=service, tracks=tracks)
