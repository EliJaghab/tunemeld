import graphene
from core.graphql.track import TrackType
from core.models.c_playlist import Playlist

from playlist_etl.constants import ServiceName


class PlaylistType(graphene.ObjectType):
    """GraphQL type for playlists with tracks."""

    genre_name = graphene.String(required=True)
    service_name = graphene.String(required=True)
    tracks = graphene.List(TrackType, required=True)


class PlaylistMetadataType(graphene.ObjectType):
    """GraphQL type for playlist metadata (for frontend display)."""

    playlist_name = graphene.String(required=True)
    playlist_cover_url = graphene.String(required=True)
    playlist_cover_description_text = graphene.String(required=True)
    playlist_url = graphene.String(required=True)
    genre_name = graphene.String(required=True)
    service_name = graphene.String(required=True)


class PlaylistQuery(graphene.ObjectType):
    service_order = graphene.List(graphene.String)
    playlist = graphene.Field(
        PlaylistType, genre=graphene.String(required=True), service=graphene.String(required=True)
    )
    playlists_by_genre = graphene.List(PlaylistMetadataType, genre=graphene.String(required=True))

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

    def resolve_playlists_by_genre(self, info, genre):
        """Get playlist metadata for all services for a given genre."""
        from core.models import Genre, Service

        try:
            Genre.objects.get(name=genre)
        except Genre.DoesNotExist:
            return []

        services = Service.objects.all()
        playlist_metadata = []

        for service in services:
            # For now, return placeholder data - this will need to be implemented
            # based on your actual playlist metadata models
            playlist_metadata.append(
                PlaylistMetadataType(
                    playlist_name=f"{service.name} {genre} Playlist",
                    playlist_cover_url=f"https://example.com/covers/{service.name}_{genre}.jpg",
                    playlist_cover_description_text=f"Curated {genre} tracks from {service.name}",
                    playlist_url=f"https://{service.name.lower()}.com/playlist/{genre}",
                    genre_name=genre,
                    service_name=service.name,
                )
            )

        return playlist_metadata
