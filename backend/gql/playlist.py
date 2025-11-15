from datetime import datetime
from typing import Any, cast

import strawberry
from core.api.genre_service_api import (
    get_all_ranks,
    get_all_raw_playlist_data_by_genre,
    get_all_services,
    get_genre,
    get_playlist_tracks_by_genre_service,
    get_service,
    get_tracks_by_isrcs,
    get_tunemeld_playlist_updated_at,
)
from core.constants import GenreName, GraphQLCacheKey, ServiceName
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import Playlist, PlaylistMetadata, RankData

from backend.gql.track import TrackType


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
    service_display_name: str
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
            return cast("list[str]", cached_result)

        service_names = [ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD, ServiceName.SPOTIFY]
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
                strawberry_track = TrackType.from_domain_track(track)
                cached_strawberry_tracks.append(strawberry_track)

            return PlaylistType(
                genre_name=cached_playlist.genre_name,
                service_name=cached_playlist.service_name,
                tracks=cached_strawberry_tracks,
            )

        genre_enum = GenreName(genre)
        service_enum = ServiceName(service)

        # Get track positions from API layer
        track_positions = get_playlist_tracks_by_genre_service(genre_enum, service_enum)

        # Batch fetch all tracks with enrichment (service sources, ranks, button labels)
        isrcs = [isrc for isrc, _position in track_positions]
        isrc_to_track = get_tracks_by_isrcs(isrcs, genre=genre_enum, service=service_enum)

        # Preserve playlist order and filter out missing tracks
        domain_tracks = []
        for isrc, _position in track_positions:
            track = isrc_to_track.get(isrc)  # type: ignore[assignment]
            if track is not None:
                domain_tracks.append(track)

        domain_playlist = Playlist(genre_name=genre, service_name=service, tracks=domain_tracks)

        redis_cache_set(CachePrefix.GQL_PLAYLIST, cache_key_data, domain_playlist.to_dict())

        # Convert domain tracks to Strawberry types
        strawberry_tracks = []
        for track in domain_tracks:
            strawberry_track = TrackType.from_domain_track(track)
            strawberry_tracks.append(strawberry_track)

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
            result = []
            metadata_list = cast("list[dict[str, Any]]", cached_result)
            for metadata in metadata_list:
                metadata_with_debug = metadata.copy()
                metadata_with_debug["debug_cache_status"] = "CACHE_HIT"
                result.append(PlaylistMetadataType(**metadata_with_debug))
            return result

        genre_enum = GenreName(genre)
        genre_obj = get_genre(genre_enum)
        if not genre_obj:
            return []

        raw_playlists = get_all_raw_playlist_data_by_genre(genre_enum)

        services = get_all_services()

        service_lookup = {service.id: service for service in services}

        playlist_metadata = []
        cache_data = []
        for raw_playlist in raw_playlists:
            service = service_lookup.get(raw_playlist.service_id)
            if service:
                domain_metadata = PlaylistMetadata.from_raw_playlist_and_service(raw_playlist, service, genre)
                metadata_dict = domain_metadata.to_dict()
                cache_data.append(metadata_dict)

                metadata_dict_with_debug = metadata_dict.copy()
                metadata_dict_with_debug["debug_cache_status"] = "CACHE_MISS"
                playlist_metadata.append(PlaylistMetadataType(**metadata_dict_with_debug))

        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, cache_data)

        return playlist_metadata

    @strawberry.field
    def updated_at(self, genre: str) -> datetime | None:
        """Get the update timestamp of the TuneMeld playlist for a genre."""
        genre_enum = GenreName(genre)
        return get_tunemeld_playlist_updated_at(genre_enum)

    @strawberry.field
    def ranks(self) -> list[RankType]:
        """Get playlist ranking options."""
        cached_result = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, GraphQLCacheKey.ALL_RANKS)

        if cached_result is not None:
            rank_list = cast("list[dict[str, Any]]", cached_result)
            return [RankType(**rank) for rank in rank_list]

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
