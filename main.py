# ruff: noqa: E402
import sys
from pathlib import Path

# Add backend directory to Python path for Django imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set up Django before any Django imports
from utils.django_setup import setup_django_safe

setup_django_safe()

# All imports after Django setup
import strawberry
from asgiref.sync import sync_to_async
from core.api.genre_service_api import (
    get_all_ranks,
    get_all_services,
    get_genre,
    get_playlist_tracks_by_genre_service,
    get_raw_playlist_data_by_genre_service,
    get_service,
    get_track_model_by_isrc,
)
from core.constants import ServiceName
from core.models.track import TrackModel
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import Playlist, RankData
from domain_types.types import PlaylistMetadata as DomainPlaylistMetadata
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
class Track:
    isrc: str
    track_name: str | None = None
    artist_name: str | None = None
    album_name: str | None = None
    spotify_url: str | None = None
    apple_music_url: str | None = None
    youtube_url: str | None = None
    soundcloud_url: str | None = None
    album_cover_url: str | None = None
    aggregate_rank: int | None = None
    aggregate_score: float | None = None
    tunemeld_rank: int | None = None

    @classmethod
    def from_django_model(cls, track_model: TrackModel, tunemeld_rank: int | None = None):
        return cls(
            isrc=track_model.isrc,
            track_name=track_model.track_name,
            artist_name=track_model.artist_name,
            album_name=track_model.album_name,
            spotify_url=track_model.spotify_url,
            apple_music_url=track_model.apple_music_url,
            youtube_url=track_model.youtube_url,
            soundcloud_url=track_model.soundcloud_url,
            album_cover_url=track_model.album_cover_url,
            aggregate_rank=track_model.aggregate_rank,
            aggregate_score=float(track_model.aggregate_score) if track_model.aggregate_score else None,
            tunemeld_rank=tunemeld_rank or getattr(track_model, "tunemeld_rank", None),
        )


@strawberry.type
class PlaylistType:
    genre_name: str
    service_name: str
    tracks: list[Track]


@strawberry.type
class PlaylistMetadata:
    playlist_name: str
    playlist_cover_url: str
    playlist_cover_description_text: str
    playlist_url: str
    genre_name: str
    service_name: str
    service_icon_url: str


@strawberry.type
class RankType:
    name: str
    display_name: str
    sort_field: str
    sort_order: str
    is_default: bool
    data_field: str


@strawberry.type
class Query:
    @strawberry.field
    async def service_order(self) -> list[str]:
        """Used to order the header art and individual playlist columns."""
        cache_key_data = "service_order"

        cached_result = await sync_to_async(redis_cache_get)(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)

        if cached_result is not None:
            return cached_result

        @sync_to_async
        def get_services_sync():
            service_names = [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value, ServiceName.SPOTIFY.value]
            services = []
            for name in service_names:
                service = get_service(name)
                if service:
                    services.append(service.name)
            return services

        services = await get_services_sync()
        await sync_to_async(redis_cache_set)(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, services)
        return services

    @strawberry.field
    async def playlist(self, genre: str, service: str) -> PlaylistType | None:
        """Get playlist data for any service (including Aggregate) and genre."""
        cache_key_data = f"resolve_playlist:genre={genre}:service={service}"

        cached_result = await sync_to_async(redis_cache_get)(CachePrefix.GQL_PLAYLIST, cache_key_data)

        if cached_result is not None:
            cached_playlist = Playlist.from_dict(cached_result)
            cached_tracks = [
                Track(
                    isrc=track.isrc,
                    track_name=track.track_name,
                    artist_name=track.artist_name,
                    album_name=track.album_name,
                    spotify_url=track.spotify_url,
                    apple_music_url=track.apple_music_url,
                    youtube_url=track.youtube_url,
                    soundcloud_url=track.soundcloud_url,
                    album_cover_url=track.album_cover_url,
                    aggregate_rank=track.aggregate_rank,
                    aggregate_score=track.aggregate_score,
                    tunemeld_rank=getattr(track, "tunemeld_rank", None),
                )
                for track in cached_playlist.tracks
            ]

            return PlaylistType(
                genre_name=cached_playlist.genre_name, service_name=cached_playlist.service_name, tracks=cached_tracks
            )

        @sync_to_async
        def get_playlist_sync():
            track_positions = get_playlist_tracks_by_genre_service(genre, service)

            django_tracks = []
            for isrc, position in track_positions:
                django_track = get_track_model_by_isrc(isrc)
                if django_track:
                    django_track.tunemeld_rank = position
                    django_tracks.append(django_track)

            return django_tracks

        django_tracks = await get_playlist_sync()

        tracks = [Track.from_django_model(track) for track in django_tracks]

        # Cache the result
        @sync_to_async
        def cache_playlist_sync():
            domain_tracks_for_cache = []
            for django_track in django_tracks:
                from core.api.genre_service_api import get_track_by_isrc

                domain_track = get_track_by_isrc(django_track.isrc)
                if domain_track:
                    domain_track.tunemeld_rank = django_track.tunemeld_rank
                    domain_tracks_for_cache.append(domain_track)

            domain_playlist = Playlist(genre_name=genre, service_name=service, tracks=domain_tracks_for_cache)
            redis_cache_set(CachePrefix.GQL_PLAYLIST, cache_key_data, domain_playlist.to_dict())

        await cache_playlist_sync()

        return PlaylistType(genre_name=genre, service_name=service, tracks=tracks)

    @strawberry.field
    async def playlists_by_genre(self, genre: str) -> list[PlaylistMetadata]:
        """Get playlist metadata for all services for a given genre."""
        cache_key_data = f"playlists_by_genre:genre={genre}"

        cached_result = await sync_to_async(redis_cache_get)(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)

        if cached_result is not None:
            return [PlaylistMetadata(**metadata) for metadata in cached_result]

        @sync_to_async
        def get_playlists_sync():
            genre_obj = get_genre(genre)
            if not genre_obj:
                return []

            raw_playlists = []
            services = get_all_services()
            for service in services:
                raw_playlist = get_raw_playlist_data_by_genre_service(genre, service.name)
                if raw_playlist:
                    raw_playlists.append((raw_playlist, service))

            playlist_metadata = []
            cache_data = []
            for raw_playlist, service in raw_playlists:
                domain_metadata = DomainPlaylistMetadata.from_raw_playlist_and_service(raw_playlist, service, genre)
                metadata_dict = domain_metadata.to_dict()
                cache_data.append(metadata_dict)
                playlist_metadata.append(PlaylistMetadata(**metadata_dict))

            redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data, cache_data)
            return playlist_metadata

        return await get_playlists_sync()

    @strawberry.field
    async def track_by_isrc(self, isrc: str) -> Track | None:
        """Get track by ISRC."""
        cache_key_data = f"track_by_isrc:{isrc}"

        cached_result = await sync_to_async(redis_cache_get)(CachePrefix.GQL_TRACK, cache_key_data)

        if cached_result is not None:
            if cached_result:
                return Track(**cached_result)
            return None

        @sync_to_async
        def get_track_sync():
            from core.api.genre_service_api import get_track_by_isrc

            domain_track = get_track_by_isrc(isrc)
            if domain_track:
                django_track = get_track_model_by_isrc(isrc)
                if django_track:
                    cache_data = {
                        "isrc": django_track.isrc,
                        "track_name": django_track.track_name,
                        "artist_name": django_track.artist_name,
                        "album_name": django_track.album_name,
                        "spotify_url": django_track.spotify_url,
                        "apple_music_url": django_track.apple_music_url,
                        "youtube_url": django_track.youtube_url,
                        "soundcloud_url": django_track.soundcloud_url,
                        "album_cover_url": django_track.album_cover_url,
                        "aggregate_rank": django_track.aggregate_rank,
                        "aggregate_score": float(django_track.aggregate_score)
                        if django_track.aggregate_score
                        else None,
                    }
                    redis_cache_set(CachePrefix.GQL_TRACK, cache_key_data, cache_data)
                    return Track.from_django_model(django_track)
                else:
                    redis_cache_set(CachePrefix.GQL_TRACK, cache_key_data, None)
            else:
                redis_cache_set(CachePrefix.GQL_TRACK, cache_key_data, None)
            return None

        return await get_track_sync()

    @strawberry.field
    async def ranks(self) -> list[RankType]:
        """Get playlist ranking options."""
        cache_key_data = "all_ranks"

        cached_result = await sync_to_async(redis_cache_get)(CachePrefix.GQL_PLAYLIST_METADATA, cache_key_data)

        if cached_result is not None:
            return [RankType(**rank) for rank in cached_result]

        @sync_to_async
        def get_ranks_sync():
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

        return await get_ranks_sync()


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI(title="TuneMeld GraphQL API")
app.include_router(graphql_app, prefix="/graphql")
app.include_router(graphql_app, prefix="/gql")


@app.get("/")
async def root():
    return {"message": "TuneMeld FastAPI GraphQL Server"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
