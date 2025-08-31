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
        from core.models import Genre
        from core.models.b_raw_playlist import RawPlaylistData

        try:
            genre_obj = Genre.objects.get(name=genre)
        except Genre.DoesNotExist:
            return []

        # Get the latest raw playlist data for each service for this genre
        raw_playlists = (
            RawPlaylistData.objects.filter(genre=genre_obj)
            .select_related("service", "genre")
            .order_by("service_id", "-created_at")
            .distinct("service_id")
        )

        playlist_metadata = []
        for raw_playlist in raw_playlists:
            # Map database service names to frontend constant names
            service_name_mapping = {
                "AppleMusic": "apple_music",
                "SoundCloud": "soundcloud",
                "Spotify": "spotify",
            }
            service_name = service_name_mapping.get(raw_playlist.service.name, raw_playlist.service.name.lower())

            playlist_metadata.append(
                PlaylistMetadataType(
                    playlist_name=raw_playlist.playlist_name or f"{raw_playlist.service.display_name} {genre} Playlist",
                    playlist_cover_url=raw_playlist.playlist_cover_url or "",
                    playlist_cover_description_text=raw_playlist.playlist_cover_description_text
                    or f"Curated {genre} tracks from {raw_playlist.service.display_name}",
                    playlist_url=raw_playlist.playlist_url,
                    genre_name=genre,
                    service_name=service_name,
                )
            )

        return playlist_metadata
