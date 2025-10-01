import graphene
from core.api.genre_service_api import (
    get_all_ranks,
    get_all_services,
    get_genre,
    get_playlist_tracks_by_genre_service,
    get_raw_playlist_data_by_genre_service,
    get_service,
    get_track_by_isrc,
    get_track_model_by_isrc,
    get_tunemeld_playlist_updated_at,
)
from core.constants import ServiceName
from core.graphql.track import TrackType
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import Playlist, PlaylistMetadata, RankData


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
    service_icon_url = graphene.String(required=True)


class RankType(graphene.ObjectType):
    """GraphQL type for ranking/sorting options."""

    name = graphene.String(required=True)
    display_name = graphene.String(required=True)
    sort_field = graphene.String(required=True)
    sort_order = graphene.String(required=True)
    is_default = graphene.Boolean(required=True)
    data_field = graphene.String(required=True)


class PlaylistQuery(graphene.ObjectType):
    service_order = graphene.List(graphene.String)
    playlist = graphene.Field(
        PlaylistType, genre=graphene.String(required=True), service=graphene.String(required=True)
    )
    playlists_by_genre = graphene.List(PlaylistMetadataType, genre=graphene.String(required=True))
    updated_at = graphene.DateTime(genre=graphene.String(required=True))
    ranks = graphene.List(RankType, description="Get playlist ranking options")

    def resolve_service_order(self, info):
        """Used to order the header art and individual playlist columns."""
        cache_key_data = "service_order"

        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)

        if cached_result is not None:
            return cached_result

        service_names = [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value, ServiceName.SPOTIFY.value]
        services = []
        for name in service_names:
            service = get_service(name)
            if service:
                services.append(service.name)

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, services)

        return services

    def resolve_playlist(self, info, genre, service):
        """Get playlist data for any service (including Aggregate) and genre."""
        cache_key_data = f"resolve_playlist:genre={genre}:service={service}"

        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST, cache_key_data)

        if cached_result is not None:
            # Reconstruct domain Playlist object from cached data
            cached_playlist = Playlist.from_dict(cached_result)

            cached_django_tracks = [track.to_django_model() for track in cached_playlist.tracks]

            return PlaylistType(
                genre_name=cached_playlist.genre_name,
                service_name=cached_playlist.service_name,
                tracks=cached_django_tracks,
            )

        # Get track positions from API layer
        track_positions = get_playlist_tracks_by_genre_service(genre, service)

        django_tracks = []
        for isrc, position in track_positions:
            django_track = get_track_model_by_isrc(isrc)
            if django_track:
                # Set the tunemeld_rank as attribute for GraphQL access
                django_track.tunemeld_rank = position
                django_tracks.append(django_track)

        # Create domain Playlist object for caching (convert Django models to domain objects)
        domain_tracks_for_cache = []
        for django_track in django_tracks:
            domain_track = get_track_by_isrc(django_track.isrc)
            if domain_track:
                domain_track.tunemeld_rank = django_track.tunemeld_rank
                domain_tracks_for_cache.append(domain_track)

        domain_playlist = Playlist(genre_name=genre, service_name=service, tracks=domain_tracks_for_cache)

        redis_cache_set(CachePrefix.GQL_PLAYLIST, cache_key_data, domain_playlist.to_dict())

        return PlaylistType(
            genre_name=genre,
            service_name=service,
            tracks=django_tracks,  # Return Django models for GraphQL compatibility
        )

    def resolve_playlists_by_genre(self, info, genre):
        """Get playlist metadata for all services for a given genre."""
        cache_key_data = f"playlists_by_genre:genre={genre}"

        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)

        if cached_result is not None:
            return [PlaylistMetadataType(**metadata) for metadata in cached_result]

        genre_obj = get_genre(genre)
        if not genre_obj:
            return []

        raw_playlists = []
        services = get_all_services()
        for service in services:
            raw_playlist = get_raw_playlist_data_by_genre_service(genre, service.name)
            if raw_playlist:
                raw_playlists.append(raw_playlist)

        playlist_metadata = []
        cache_data = []
        for raw_playlist in raw_playlists:
            # Find the service for this raw_playlist
            service = next((s for s in services if s.id == raw_playlist.service_id), None)
            if service:
                domain_metadata = PlaylistMetadata.from_raw_playlist_and_service(raw_playlist, service, genre)
                metadata_dict = domain_metadata.to_dict()
                cache_data.append(metadata_dict)
                playlist_metadata.append(PlaylistMetadataType(**metadata_dict))

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, cache_data)

        return playlist_metadata

    def resolve_updated_at(self, info, genre):
        """Get the update timestamp of the TuneMeld playlist for a genre."""
        return get_tunemeld_playlist_updated_at(genre)

    def resolve_ranks(self, info):
        """Get playlist ranking options."""
        cache_key_data = "all_ranks"

        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)

        if cached_result is not None:
            return [RankType(**rank) for rank in cached_result]

        domain_ranks = get_all_ranks()

        cache_data = []
        rank_types = []
        for rank in domain_ranks:
            domain_rank = RankData.from_rank(rank)
            rank_dict = domain_rank.to_dict()
            cache_data.append(rank_dict)
            rank_types.append(RankType(**rank_dict))

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, cache_data)

        return rank_types
