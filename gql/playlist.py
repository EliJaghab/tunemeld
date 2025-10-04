from datetime import datetime

import strawberry
from core.api.genre_service_api import (
    get_all_ranks,
    get_all_raw_playlist_data_by_genre,
    get_all_services,
    get_genre,
    get_playlist_tracks_by_genre_service,
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
    debug_cache_status: str | None = None


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
        for isrc, _position in track_positions:
            django_track = get_track_model_by_isrc(isrc)
            if django_track:
                django_tracks.append(django_track)

        # Create domain Playlist object for caching (convert Django models to domain objects)
        domain_tracks_for_cache = []
        for django_track in django_tracks:
            domain_track = get_track_by_isrc(django_track.isrc)
            if domain_track:
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
        import time

        start_time = time.time()

        cache_key_data = GraphQLCacheKey.playlists_by_genre(genre)
        print(f"[PERF] playlists_by_genre starting for genre='{genre}', cache_key='{cache_key_data}'")

        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)
        cache_lookup_time = time.time()
        cache_status = "HIT" if cached_result else "MISS"
        print(f"[PERF] Cache lookup took {(cache_lookup_time - start_time) * 1000:.2f}ms, cached_result={cache_status}")

        if cached_result is not None:
            result = []
            for metadata in cached_result:
                metadata_with_debug = metadata.copy()
                metadata_with_debug["debug_cache_status"] = f"CACHE_HIT_at_{cache_lookup_time:.3f}"
                result.append(PlaylistMetadataType(**metadata_with_debug))
            total_time = time.time()
            print(f"[PERF] Cache HIT - Total time: {(total_time - start_time) * 1000:.2f}ms")
            return result

        genre_obj = get_genre(genre)
        if not genre_obj:
            print(f"[PERF] Genre '{genre}' not found")
            return []

        genre_lookup_time = time.time()
        print(f"[PERF] Genre lookup took {(genre_lookup_time - cache_lookup_time) * 1000:.2f}ms")

        # Use optimized bulk query instead of N+1 loop
        raw_playlists = get_all_raw_playlist_data_by_genre(genre)
        raw_playlists_time = time.time()
        duration = (raw_playlists_time - genre_lookup_time) * 1000
        print(f"[PERF] get_all_raw_playlist_data_by_genre took {duration:.2f}ms, found {len(raw_playlists)} playlists")

        # Get services once for mapping
        services = get_all_services()
        services_time = time.time()
        duration = (services_time - raw_playlists_time) * 1000
        print(f"[PERF] get_all_services took {duration:.2f}ms, found {len(services)} services")

        service_lookup = {service.id: service for service in services}

        playlist_metadata = []
        cache_data = []
        for raw_playlist in raw_playlists:
            # Use lookup instead of linear search
            service = service_lookup.get(raw_playlist.service_id)
            if service:
                domain_metadata = PlaylistMetadata.from_raw_playlist_and_service(raw_playlist, service, genre)
                metadata_dict = domain_metadata.to_dict()
                cache_data.append(metadata_dict)

                # Add debug info for cache miss
                metadata_dict_with_debug = metadata_dict.copy()
                current_time = time.time()
                metadata_dict_with_debug["debug_cache_status"] = (
                    f"CACHE_MISS_at_{current_time:.3f}_took_{(current_time - start_time) * 1000:.0f}ms"
                )
                playlist_metadata.append(PlaylistMetadataType(**metadata_dict_with_debug))

        processing_time = time.time()
        print(f"[PERF] Metadata processing took {(processing_time - services_time) * 1000:.2f}ms")

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, cache_data)
        cache_set_time = time.time()
        print(f"[PERF] Cache set took {(cache_set_time - processing_time) * 1000:.2f}ms")

        total_time = time.time()
        print(f"[PERF] playlists_by_genre TOTAL time: {(total_time - start_time) * 1000:.2f}ms")

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
