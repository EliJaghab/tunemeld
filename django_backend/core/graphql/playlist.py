import graphene
from core.graphql.track import TrackType
from core.models import Genre, Track
from core.models.d_raw_playlist import RawPlaylistData
from core.models.e_playlist import Playlist
from core.utils.constants import ServiceName


class PlaylistType(graphene.ObjectType):
    """GraphQL type for playlists with tracks."""

    genre_name = graphene.String(required=True)
    service_name = graphene.String(required=True)
    tracks = graphene.List(TrackType, required=True)
    updated_at = graphene.DateTime()


class PlaylistMetadataType(graphene.ObjectType):
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
    updated_at = graphene.DateTime(genre=graphene.String(required=True))

    def resolve_service_order(self, info):
        """Used to order the header art."""
        return [ServiceName.SOUNDCLOUD, ServiceName.APPLE_MUSIC, ServiceName.SPOTIFY]

    def resolve_playlist(self, info, genre, service):
        """Get playlist data for any service (including Aggregate) and genre."""
        playlists = Playlist.objects.filter(genre__name=genre, service__name=service).order_by("position")

        tracks = []
        for playlist_entry in playlists:
            if playlist_entry.isrc:
                try:
                    track = Track.objects.get(isrc=playlist_entry.isrc)
                    tracks.append(track)
                except Track.DoesNotExist:
                    continue

        return PlaylistType(genre_name=genre, service_name=service, tracks=tracks)

    def resolve_playlists_by_genre(self, info, genre):
        """Get playlist metadata for all services for a given genre."""
        try:
            genre_obj = Genre.objects.get(name=genre)
        except Genre.DoesNotExist:
            return []

        raw_playlists = (
            RawPlaylistData.objects.filter(genre=genre_obj)
            .select_related("service", "genre")
            .order_by("service", "-created_at")
            .distinct("service")
        )

        playlist_metadata = []
        for raw_playlist in raw_playlists:
            playlist_metadata.append(
                PlaylistMetadataType(
                    playlist_name=raw_playlist.playlist_name or f"{raw_playlist.service.display_name} {genre} Playlist",
                    playlist_cover_url=raw_playlist.playlist_cover_url or "",
                    playlist_cover_description_text=raw_playlist.playlist_cover_description_text
                    or f"Curated {genre} tracks from {raw_playlist.service.display_name}",
                    playlist_url=raw_playlist.playlist_url,
                    genre_name=genre,
                    service_name=raw_playlist.service.name,
                )
            )

        return playlist_metadata

    def resolve_updated_at(self, info, genre):
        """Get the update timestamp of the TuneMeld playlist for a genre."""
        playlist_entry = (
            Playlist.objects.filter(genre__name=genre, service__name=ServiceName.TUNEMELD)
            .select_related("service_track__track")
            .first()
        )

        if playlist_entry and playlist_entry.service_track and playlist_entry.service_track.track:
            return playlist_entry.service_track.track.updated_at

        return None
