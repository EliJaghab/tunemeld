from datetime import datetime

import strawberry
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
from core.constants import GraphQLCacheKey, ServiceName
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import Playlist, PlaylistMetadata, RankData

from gql.track import TrackType


@strawberry.type
class PlaylistType:
    """GraphQL type for playlists with tracks."""

    genre_name: str
    service_name: str
    tracks: list[TrackType]
    updated_at: datetime | None = None


@strawberry.type
class PlaylistMetadataType:
    playlist_name: str
    playlist_cover_url: str
    playlist_cover_description_text: str
    playlist_url: str
    genre_name: str
    service_name: str
    service_icon_url: str


@strawberry.type
class RankType:
    """GraphQL type for ranking/sorting options."""

    name: str
    display_name: str
    sort_field: str
    sort_order: str
    is_default: bool
    data_field: str


@strawberry.type
class PlaylistQuery:
    @strawberry.field
    def service_order(self) -> list[str]:
        """Used to order the header art and individual playlist columns."""
        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, GraphQLCacheKey.SERVICE_ORDER)

        if cached_result is not None:
            return cached_result

        service_names = [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value, ServiceName.SPOTIFY.value]
        services = []
        for name in service_names:
            service = get_service(name)
            if service:
                services.append(service.name)

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, GraphQLCacheKey.SERVICE_ORDER, services)

        return services

    @strawberry.field
    def playlist(self, genre: str, service: str) -> PlaylistType | None:
        """Get playlist data for any service (including Aggregate) and genre."""
        cache_key_data = GraphQLCacheKey.resolve_playlist(genre, service)

        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST, cache_key_data)

        if cached_result is not None:
            # Reconstruct domain Playlist object from cached data
            cached_playlist = Playlist.from_dict(cached_result)

            cached_strawberry_tracks = []
            for track in cached_playlist.tracks:
                django_track = track.to_django_model()
                strawberry_track = TrackType.from_django_model(django_track)
                cached_strawberry_tracks.append(strawberry_track)

            return PlaylistType(
                genre_name=cached_playlist.genre_name,
                service_name=cached_playlist.service_name,
                tracks=cached_strawberry_tracks,
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

        # Convert Django models to Strawberry types
        strawberry_tracks = [TrackType.from_django_model(django_track) for django_track in django_tracks]

        return PlaylistType(
            genre_name=genre,
            service_name=service,
            tracks=strawberry_tracks,
        )

    @strawberry.field
    def playlists_by_genre(self, genre: str) -> list[PlaylistMetadataType]:
        """Get playlist metadata for all services for a given genre."""
        cache_key_data = GraphQLCacheKey.playlists_by_genre(genre)

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

    @strawberry.field
    def updated_at(self, genre: str) -> datetime | None:
        """Get the update timestamp of the TuneMeld playlist for a genre."""
        return get_tunemeld_playlist_updated_at(genre)

    @strawberry.field
    def ranks(self) -> list[RankType]:
        """Get playlist ranking options."""
        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, GraphQLCacheKey.ALL_RANKS)

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

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, GraphQLCacheKey.ALL_RANKS, cache_data)

        return rank_types
