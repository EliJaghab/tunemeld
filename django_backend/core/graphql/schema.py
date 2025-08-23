import graphene
from core.models.c_playlist import Playlist
from core.models.d_track import Track
from core.models.view_counts import ViewCount
from graphene_django import DjangoObjectType


class TrackType(DjangoObjectType):
    view_counts = graphene.JSONString()

    class Meta:
        model = Track
        fields = "__all__"

    def resolve_view_counts(self, info):
        view_counts = ViewCount.objects.filter(isrc=self.isrc).select_related("service")
        return {vc.service.name: vc.view_count for vc in view_counts}


class PlaylistType(graphene.ObjectType):
    genre_name = graphene.String()
    service_name = graphene.String()
    playlist_name = graphene.String()
    playlist_cover_url = graphene.String()
    playlist_url = graphene.String()
    tracks = graphene.List(TrackType)


class Query(graphene.ObjectType):
    track = graphene.Field(TrackType, isrc=graphene.String(required=True))
    playlist = graphene.Field(
        PlaylistType, genre_name=graphene.String(required=True), service_name=graphene.String(required=True)
    )

    def resolve_track(self, info, isrc):
        try:
            return Track.objects.get(isrc=isrc)
        except Track.DoesNotExist:
            return None

    def resolve_playlist(self, info, genre_name, service_name):
        from core.models.b_raw_playlist import RawPlaylistData

        # Get playlist positions
        playlist_positions = (
            Playlist.objects.filter(genre__name=genre_name, service__name=service_name)
            .select_related("service_track", "genre", "service")
            .order_by("position")
        )

        if not playlist_positions.exists():
            return None

        # Get playlist metadata
        try:
            raw_playlist = RawPlaylistData.objects.get(genre__name=genre_name, service__name=service_name)
            playlist_name = raw_playlist.playlist_name
            playlist_cover_url = raw_playlist.playlist_cover_url
            playlist_url = raw_playlist.playlist_url
        except RawPlaylistData.DoesNotExist:
            playlist_name = ""
            playlist_cover_url = ""
            playlist_url = ""

        # Build tracks list
        tracks = []
        for position in playlist_positions:
            if position.isrc:
                try:
                    track = Track.objects.get(isrc=position.isrc)
                    tracks.append(track)
                except Track.DoesNotExist:
                    pass

        return PlaylistType(
            genre_name=genre_name,
            service_name=service_name,
            playlist_name=playlist_name,
            playlist_cover_url=playlist_cover_url,
            playlist_url=playlist_url,
            tracks=tracks,
        )


schema = graphene.Schema(query=Query)
