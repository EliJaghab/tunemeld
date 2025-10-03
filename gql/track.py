from datetime import datetime

import strawberry
from core.api.genre_service_api import (
    get_service,
    get_track_by_isrc,
    get_track_model_by_isrc,
    get_track_rank_by_track_object,
)
from core.api.track_metadata_api import build_track_query_url
from core.constants import GraphQLCacheKey, ServiceName
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from core.utils.utils import truncate_to_words

from gql.button_labels import ButtonLabelType, generate_track_button_labels
from gql.service import ServiceType


@strawberry.type
class TrackType:
    id: int
    isrc: str
    album_name: str | None = None
    spotify_url: str | None = None
    apple_music_url: str | None = None
    youtube_url: str | None = None
    soundcloud_url: str | None = None
    album_cover_url: str | None = None
    aggregate_rank: int | None = None
    aggregate_score: float | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_cached_dict(cls, cached_data: dict) -> "TrackType":
        """Create TrackType from cached dictionary data."""
        track = cls(
            id=cached_data["id"],
            isrc=cached_data["isrc"],
            album_name=cached_data["album_name"],
            spotify_url=cached_data["spotify_url"],
            apple_music_url=cached_data["apple_music_url"],
            youtube_url=cached_data["youtube_url"],
            soundcloud_url=cached_data["soundcloud_url"],
            album_cover_url=cached_data["album_cover_url"],
            aggregate_rank=cached_data["aggregate_rank"],
            aggregate_score=cached_data["aggregate_score"],
            updated_at=(datetime.fromisoformat(cached_data["updated_at"]) if cached_data["updated_at"] else None),
        )
        track._track_name = cached_data.get("track_name")
        track._artist_name = cached_data.get("artist_name")
        return track

    @classmethod
    def from_django_model(cls, django_track) -> "TrackType":
        """Create TrackType from Django TrackModel."""
        track = cls(
            id=django_track.id,
            isrc=django_track.isrc,
            album_name=django_track.album_name,
            spotify_url=django_track.spotify_url,
            apple_music_url=django_track.apple_music_url,
            youtube_url=django_track.youtube_url,
            soundcloud_url=django_track.soundcloud_url,
            album_cover_url=django_track.album_cover_url,
            aggregate_rank=django_track.aggregate_rank,
            aggregate_score=django_track.aggregate_score,
            updated_at=django_track.updated_at,
        )
        track._track_name = django_track.track_name
        track._artist_name = django_track.artist_name

        return track

    @classmethod
    def to_cache_dict(cls, django_track) -> dict:
        """Create cache dictionary from Django TrackModel."""
        return {
            "id": django_track.id,
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
            "aggregate_score": django_track.aggregate_score,
            "updated_at": str(django_track.updated_at) if django_track.updated_at else None,
        }

    @strawberry.field(description="Track name truncated to 30 characters at word boundaries")
    def track_name(self) -> str | None:
        return truncate_to_words(self._track_name, 30) if hasattr(self, "_track_name") and self._track_name else None

    @strawberry.field(description="Artist name truncated to 30 characters at word boundaries")
    def artist_name(self) -> str | None:
        return truncate_to_words(self._artist_name, 30) if hasattr(self, "_artist_name") and self._artist_name else None

    @strawberry.field(description="Complete track name without truncation")
    def full_track_name(self) -> str | None:
        return getattr(self, "_track_name", None)

    @strawberry.field(description="Complete artist name without truncation")
    def full_artist_name(self) -> str | None:
        return getattr(self, "_artist_name", None)

    @strawberry.field(description="Contextual button labels for this track")
    def button_labels(self, info) -> list[ButtonLabelType]:
        if hasattr(self, "_button_labels"):
            return [
                ButtonLabelType(
                    button_type=bl["buttonType"],
                    context=bl["context"],
                    title=bl["title"],
                    aria_label=bl["ariaLabel"],
                )
                for bl in self._button_labels
            ]

        genre = info.variable_values.get("genre")
        service = info.variable_values.get("service")
        return generate_track_button_labels(self, genre=genre, service=service)

    @strawberry.field(description="Internal URL for this track with genre/rank/player context")
    def track_detail_url(self, genre: str, rank: str, player: str) -> str:
        cache_key = f"track_detail_url_{player}"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)

        return build_track_query_url(genre, rank, self.isrc, player)

    @strawberry.field(description="Position in the TuneMeld playlist for current genre")
    def tunemeld_rank(self, info) -> int | None:
        genre_name = info.variable_values["genre"]
        track_domain = get_track_by_isrc(self.isrc)
        if not track_domain:
            return None
        return get_track_rank_by_track_object(track_domain, genre_name, ServiceName.TUNEMELD.value)

    @strawberry.field(description="Position on SoundCloud playlist for current genre")
    def soundcloud_rank(self, info) -> int | None:
        if hasattr(self, "_soundcloud_rank"):
            return self._soundcloud_rank

        genre_name = info.variable_values["genre"]
        track_domain = get_track_by_isrc(self.isrc)
        if not track_domain:
            return None
        return get_track_rank_by_track_object(track_domain, genre_name, ServiceName.SOUNDCLOUD.value)

    @strawberry.field(description="Position on Spotify playlist for current genre")
    def spotify_rank(self, info) -> int | None:
        if hasattr(self, "_spotify_rank"):
            return self._spotify_rank

        genre_name = info.variable_values["genre"]
        track_domain = get_track_by_isrc(self.isrc)
        if not track_domain:
            return None
        return get_track_rank_by_track_object(track_domain, genre_name, ServiceName.SPOTIFY.value)

    @strawberry.field(description="Position on Apple Music playlist for current genre")
    def apple_music_rank(self, info) -> int | None:
        if hasattr(self, "_apple_music_rank"):
            return self._apple_music_rank

        genre_name = info.variable_values["genre"]
        track_domain = get_track_by_isrc(self.isrc)
        if not track_domain:
            return None
        return get_track_rank_by_track_object(track_domain, genre_name, ServiceName.APPLE_MUSIC.value)

    @strawberry.field(description="Spotify service source with metadata")
    def spotify_source(self) -> ServiceType | None:
        if hasattr(self, "_spotify_source") and self._spotify_source:
            return ServiceType(
                name=self._spotify_source["name"],
                display_name=self._spotify_source["display_name"],
                url=self._spotify_source["url"],
                icon_url=self._spotify_source["icon_url"],
            )

        if not self.spotify_url:
            return None
        service = get_service(ServiceName.SPOTIFY)
        if service:
            return ServiceType(
                name=ServiceName.SPOTIFY.value,
                display_name=service.display_name,
                url=self.spotify_url,
                icon_url=service.icon_url,
            )
        return None

    @strawberry.field(description="Apple Music service source with metadata")
    def apple_music_source(self) -> ServiceType | None:
        if hasattr(self, "_apple_music_source") and self._apple_music_source:
            return ServiceType(
                name=self._apple_music_source["name"],
                display_name=self._apple_music_source["display_name"],
                url=self._apple_music_source["url"],
                icon_url=self._apple_music_source["icon_url"],
            )

        if not self.apple_music_url:
            return None
        service = get_service(ServiceName.APPLE_MUSIC)
        if service:
            return ServiceType(
                name=ServiceName.APPLE_MUSIC.value,
                display_name=service.display_name,
                url=self.apple_music_url,
                icon_url=service.icon_url,
            )
        return None

    @strawberry.field(description="SoundCloud service source with metadata")
    def soundcloud_source(self) -> ServiceType | None:
        if hasattr(self, "_soundcloud_source") and self._soundcloud_source:
            return ServiceType(
                name=self._soundcloud_source["name"],
                display_name=self._soundcloud_source["display_name"],
                url=self._soundcloud_source["url"],
                icon_url=self._soundcloud_source["icon_url"],
            )

        if not self.soundcloud_url:
            return None
        service = get_service(ServiceName.SOUNDCLOUD)
        if service:
            return ServiceType(
                name=ServiceName.SOUNDCLOUD.value,
                display_name=service.display_name,
                url=self.soundcloud_url,
                icon_url=service.icon_url,
            )
        return None

    @strawberry.field(description="YouTube service source with metadata")
    def youtube_source(self) -> ServiceType | None:
        if hasattr(self, "_youtube_source") and self._youtube_source:
            return ServiceType(
                name=self._youtube_source["name"],
                display_name=self._youtube_source["display_name"],
                url=self._youtube_source["url"],
                icon_url=self._youtube_source["icon_url"],
            )

        if not self.youtube_url:
            return None
        service = get_service(ServiceName.YOUTUBE)
        if service:
            return ServiceType(
                name=ServiceName.YOUTUBE.value,
                display_name=service.display_name,
                url=self.youtube_url,
                icon_url=service.icon_url,
            )
        return None


@strawberry.type
class TrackQuery:
    @strawberry.field
    def track_by_isrc(self, isrc: str) -> TrackType | None:
        cache_key_data = GraphQLCacheKey.track_by_isrc(isrc)

        cached_result = redis_cache_get(CachePrefix.GQL_TRACK, cache_key_data)

        if cached_result is not None:
            return TrackType.from_cached_dict(cached_result) if cached_result else None

        domain_track = get_track_by_isrc(isrc)
        if domain_track:
            django_track = get_track_model_by_isrc(isrc)
            if django_track:
                cache_data = TrackType.to_cache_dict(django_track)
                redis_cache_set(CachePrefix.GQL_TRACK, cache_key_data, cache_data)
                return TrackType.from_django_model(django_track)
            else:
                redis_cache_set(CachePrefix.GQL_TRACK, cache_key_data, None)
        else:
            redis_cache_set(CachePrefix.GQL_TRACK, cache_key_data, None)

        return None
