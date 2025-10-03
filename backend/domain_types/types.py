"""
Domain models for TuneMeld - pure business logic without Django dependencies.

These models mirror the frontend TypeScript types exactly and provide
clean serialization/deserialization for GraphQL and cache layers.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

from core.constants import ServiceName
from core.utils.utils import format_percentage_change, format_play_count
from pydantic import BaseModel, Field


# ETL and domain types
class NormalizedTrack(BaseModel):
    """Normalized track data for Phase C - maps to Track model fields."""

    position: int
    isrc: str | None = None
    name: str
    artist: str
    album: str | None = None
    spotify_url: str | None = None
    apple_music_url: str | None = None
    soundcloud_url: str | None = None
    album_cover_url: str | None = None

    @property
    def service_url(self) -> str:
        """Get the service-specific URL for this track."""
        return self.spotify_url or self.apple_music_url or self.soundcloud_url or ""


class ButtonLabel(BaseModel):
    button_type: str
    context: str | None = None
    title: str | None = None
    aria_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "button_type": self.button_type,
            "context": self.context,
            "title": self.title,
            "aria_label": self.aria_label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            button_type=data["buttonType"],
            context=data.get("context"),
            title=data.get("title"),
            aria_label=data.get("ariaLabel"),
        )


class ServiceSource(BaseModel):
    name: str
    display_name: str
    url: str
    icon_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "url": self.url,
            "iconUrl": self.icon_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            name=data["name"],
            display_name=data["displayName"],
            url=data["url"],
            icon_url=data["iconUrl"],
        )


class Track(BaseModel):
    """Domain model for Track - matches frontend TypeScript interface exactly."""

    # Core track data
    isrc: str
    track_name: str
    artist_name: str
    full_track_name: str
    full_artist_name: str
    album_name: str | None = None
    album_cover_url: str | None = None

    # Service URLs
    spotify_url: str | None = None
    apple_music_url: str | None = None
    soundcloud_url: str | None = None
    youtube_url: str | None = None

    # Rankings
    tunemeld_rank: int
    spotify_rank: int | None = None
    apple_music_rank: int | None = None
    soundcloud_rank: int | None = None

    # Service sources
    spotify_source: ServiceSource | None = None
    apple_music_source: ServiceSource | None = None
    soundcloud_source: ServiceSource | None = None
    youtube_source: ServiceSource | None = None

    # Detail URLs
    track_detail_url_spotify: str | None = None
    track_detail_url_apple_music: str | None = None
    track_detail_url_soundcloud: str | None = None
    track_detail_url_youtube: str | None = None

    # Play count data (dynamically added)
    total_current_play_count: int | None = None
    total_weekly_change_percentage: float | None = None
    spotify_current_play_count: int | None = None
    youtube_current_play_count: int | None = None

    # UI helpers
    button_labels: list[ButtonLabel] = Field(default_factory=list)

    # Django model fields (for Django model conversion)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_django_model(self):
        """Convert domain Track to Django TrackModel for GraphQL compatibility."""
        # Import inside method to avoid circular dependency
        from core.models.track import TrackModel

        if self.id:
            try:
                django_track = TrackModel.objects.get(id=self.id)
                django_track.track_name = self.track_name
                django_track.artist_name = self.artist_name
                django_track.album_name = self.album_name
                django_track.album_cover_url = self.album_cover_url
                django_track.spotify_url = self.spotify_url
                django_track.apple_music_url = self.apple_music_url
                django_track.soundcloud_url = self.soundcloud_url
                django_track.youtube_url = self.youtube_url
                return django_track
            except TrackModel.DoesNotExist:
                pass

        return TrackModel(
            id=self.id,
            isrc=self.isrc,
            track_name=self.track_name,
            artist_name=self.artist_name,
            album_name=self.album_name,
            album_cover_url=self.album_cover_url,
            spotify_url=self.spotify_url,
            apple_music_url=self.apple_music_url,
            soundcloud_url=self.soundcloud_url,
            youtube_url=self.youtube_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to frontend-compatible dict with camelCase keys."""
        return {
            "tunemeldRank": self.tunemeld_rank,
            "spotifyRank": self.spotify_rank,
            "appleMusicRank": self.apple_music_rank,
            "soundcloudRank": self.soundcloud_rank,
            "isrc": self.isrc,
            "trackName": self.track_name,
            "artistName": self.artist_name,
            "fullTrackName": self.full_track_name,
            "fullArtistName": self.full_artist_name,
            "albumName": self.album_name,
            "albumCoverUrl": self.album_cover_url,
            "youtubeUrl": self.youtube_url,
            "spotifyUrl": self.spotify_url,
            "appleMusicUrl": self.apple_music_url,
            "soundcloudUrl": self.soundcloud_url,
            "buttonLabels": [bl.to_dict() for bl in self.button_labels],
            "spotifySource": self.spotify_source.to_dict() if self.spotify_source else None,
            "appleMusicSource": self.apple_music_source.to_dict() if self.apple_music_source else None,
            "soundcloudSource": self.soundcloud_source.to_dict() if self.soundcloud_source else None,
            "youtubeSource": self.youtube_source.to_dict() if self.youtube_source else None,
            "trackDetailUrlSpotify": self.track_detail_url_spotify,
            "trackDetailUrlAppleMusic": self.track_detail_url_apple_music,
            "trackDetailUrlSoundcloud": self.track_detail_url_soundcloud,
            "trackDetailUrlYoutube": self.track_detail_url_youtube,
            "totalCurrentPlayCount": self.total_current_play_count,
            "totalWeeklyChangePercentage": self.total_weekly_change_percentage,
            "spotifyCurrentPlayCount": self.spotify_current_play_count,
            "youtubeCurrentPlayCount": self.youtube_current_play_count,
            # Django fields for internal use
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Convert from frontend-compatible dict with camelCase keys."""
        return cls(
            tunemeld_rank=data["tunemeldRank"],
            spotify_rank=data.get("spotifyRank"),
            apple_music_rank=data.get("appleMusicRank"),
            soundcloud_rank=data.get("soundcloudRank"),
            isrc=data["isrc"],
            track_name=data["trackName"],
            artist_name=data["artistName"],
            full_track_name=data["fullTrackName"],
            full_artist_name=data["fullArtistName"],
            album_name=data.get("albumName"),
            album_cover_url=data.get("albumCoverUrl"),
            youtube_url=data.get("youtubeUrl"),
            spotify_url=data.get("spotifyUrl"),
            apple_music_url=data.get("appleMusicUrl"),
            soundcloud_url=data.get("soundcloudUrl"),
            button_labels=[ButtonLabel.from_dict(bl) for bl in data.get("buttonLabels", [])],
            spotify_source=ServiceSource.from_dict(data["spotifySource"]) if data.get("spotifySource") else None,
            apple_music_source=ServiceSource.from_dict(data["appleMusicSource"])
            if data.get("appleMusicSource")
            else None,
            soundcloud_source=ServiceSource.from_dict(data["soundcloudSource"])
            if data.get("soundcloudSource")
            else None,
            youtube_source=ServiceSource.from_dict(data["youtubeSource"]) if data.get("youtubeSource") else None,
            track_detail_url_spotify=data.get("trackDetailUrlSpotify"),
            track_detail_url_apple_music=data.get("trackDetailUrlAppleMusic"),
            track_detail_url_soundcloud=data.get("trackDetailUrlSoundcloud"),
            track_detail_url_youtube=data.get("trackDetailUrlYoutube"),
            total_current_play_count=data.get("totalCurrentPlayCount"),
            total_weekly_change_percentage=data.get("totalWeeklyChangePercentage"),
            spotify_current_play_count=data.get("spotifyCurrentPlayCount"),
            youtube_current_play_count=data.get("youtubeCurrentPlayCount"),
            # Django fields
            id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )

    @classmethod
    def from_django_model(cls, django_track, genre: str | None = None, service: str | None = None) -> Self:
        """Convert from Django TrackModel with full enrichment."""
        # Import inside method to avoid circular dependency

        # Base track data from Django model
        track_data = {
            "id": django_track.id,
            "isrc": django_track.isrc,
            "trackName": django_track.track_name,
            "artistName": django_track.artist_name,
            "fullTrackName": django_track.track_name,  # Default to track_name
            "fullArtistName": django_track.artist_name,  # Default to artist_name
            "albumName": django_track.album_name,
            "albumCoverUrl": django_track.album_cover_url,
            "spotifyUrl": django_track.spotify_url,
            "appleMusicUrl": django_track.apple_music_url,
            "soundcloudUrl": django_track.soundcloud_url,
            "youtubeUrl": django_track.youtube_url,
            "tunemeldRank": getattr(django_track, "tunemeld_rank", 0),
            "created_at": django_track.created_at.isoformat() if django_track.created_at else None,
            "updated_at": django_track.updated_at.isoformat() if django_track.updated_at else None,
        }

        # Add enrichment if genre/service provided
        if genre and service:
            enriched_data = cls._enrich_track_data(django_track, genre, service)
            track_data.update(enriched_data)

        return cls.from_dict(track_data)

    @classmethod
    def _enrich_track_data(cls, track, genre: str, service: str) -> dict[str, Any]:
        """Enrich track with computed fields."""
        from core.constants import ServiceName

        enrichment: dict[str, Any] = {}

        # Service sources
        for service_name in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD, ServiceName.YOUTUBE]:
            source_key = f"{service_name.value.replace('_', '')}Source"
            enrichment[source_key] = cls._build_service_source(track, service_name)

        # Service rankings
        enrichment.update(
            {
                "spotifyRank": cls._get_service_rank(track, genre, ServiceName.SPOTIFY),
                "appleMusicRank": cls._get_service_rank(track, genre, ServiceName.APPLE_MUSIC),
                "soundcloudRank": cls._get_service_rank(track, genre, ServiceName.SOUNDCLOUD),
            }
        )

        # Track detail URLs
        for player in ["spotify", "apple_music", "soundcloud", "youtube"]:
            url_key = f"trackDetailUrl{player.replace('_', '').title()}"
            enrichment[url_key] = cls._build_track_detail_url(track, genre, player)

        # Button labels
        enrichment["buttonLabels"] = cls._get_button_labels(track, genre, service)

        return enrichment

    @staticmethod
    def _build_service_source(track, service_name: ServiceName) -> ServiceSource | None:
        """Build service source object."""
        from core.api.genre_service_api import get_service

        url_field = f"{service_name.value}_url"
        track_url = getattr(track, url_field, None)

        if not track_url:
            return None

        try:
            service = get_service(service_name)
            if not service:
                return None
            return ServiceSource(
                name=service_name.value,
                display_name=service.display_name,
                url=track_url,
                icon_url=service.icon_url,
            )
        except Exception:
            return None

    @staticmethod
    def _get_service_rank(track, genre: str, service_name: ServiceName) -> int | None:
        """Get track rank for service/genre."""
        from core.api.genre_service_api import get_track_rank_by_track_object

        try:
            return get_track_rank_by_track_object(track, genre, service_name.value)
        except Exception:
            return None

    @staticmethod
    def _build_track_detail_url(track, genre: str, player: str) -> str:
        """Build track detail URL for player."""
        from core.api.track_metadata_api import build_track_query_url

        try:
            url = build_track_query_url(genre, "tunemeld-rank", track.isrc, player)
            return url if url else f"/?genre={genre}&rank=tunemeld-rank&player={player}&isrc={track.isrc}"
        except Exception:
            return f"/?genre={genre}&rank=tunemeld-rank&player={player}&isrc={track.isrc}"

    @staticmethod
    def _get_button_labels(track, genre: str, service: str) -> list[ButtonLabel]:
        """Get button labels for track."""
        try:
            from gql.button_labels import generate_track_button_labels

            button_labels = generate_track_button_labels(track, genre=genre, service=service)
            if button_labels:
                return [
                    ButtonLabel(button_type=bl.buttonType, context=bl.context, title=bl.title, aria_label=bl.ariaLabel)
                    for bl in button_labels
                ]
        except Exception:
            pass
        return []


class Playlist(BaseModel):
    """Domain model for Playlist - matches frontend TypeScript interface exactly."""

    genre_name: str
    service_name: str
    tracks: list[Track] = Field(default_factory=list)
    playlist_name: str | None = None
    playlist_cover_url: str | None = None
    playlist_cover_description_text: str | None = None
    playlist_url: str | None = None
    service_icon_url: str | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to frontend-compatible dict with camelCase keys."""
        return {
            "genreName": self.genre_name,
            "serviceName": self.service_name,
            "tracks": [track.to_dict() for track in self.tracks],
            "playlistName": self.playlist_name,
            "playlistCoverUrl": self.playlist_cover_url,
            "playlistCoverDescriptionText": self.playlist_cover_description_text,
            "playlistUrl": self.playlist_url,
            "serviceIconUrl": self.service_icon_url,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Convert from frontend-compatible dict with camelCase keys."""
        return cls(
            genre_name=data["genreName"],
            service_name=data["serviceName"],
            tracks=[Track.from_dict(track_data) for track_data in data.get("tracks", [])],
            playlist_name=data.get("playlistName"),
            playlist_cover_url=data.get("playlistCoverUrl"),
            playlist_cover_description_text=data.get("playlistCoverDescriptionText"),
            playlist_url=data.get("playlistUrl"),
            service_icon_url=data.get("serviceIconUrl"),
            updated_at=datetime.fromisoformat(data["updatedAt"]) if data.get("updatedAt") else None,
        )


class PlayCount(BaseModel):
    """Domain model for PlayCount data."""

    isrc: str
    youtube_current_play_count: int | None = None
    spotify_current_play_count: int | None = None
    total_current_play_count: int | None = None
    youtube_current_play_count_abbreviated: str | None = None
    spotify_current_play_count_abbreviated: str | None = None
    total_current_play_count_abbreviated: str | None = None
    total_weekly_change_percentage: float | None = None
    total_weekly_change_percentage_formatted: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "isrc": self.isrc,
            "youtubeCurrentPlayCount": self.youtube_current_play_count,
            "spotifyCurrentPlayCount": self.spotify_current_play_count,
            "totalCurrentPlayCount": self.total_current_play_count,
            "youtubeCurrentPlayCountAbbreviated": self.youtube_current_play_count_abbreviated,
            "spotifyCurrentPlayCountAbbreviated": self.spotify_current_play_count_abbreviated,
            "totalCurrentPlayCountAbbreviated": self.total_current_play_count_abbreviated,
            "totalWeeklyChangePercentage": self.total_weekly_change_percentage,
            "totalWeeklyChangePercentageFormatted": self.total_weekly_change_percentage_formatted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            isrc=data["isrc"],
            youtube_current_play_count=data.get("youtubeCurrentPlayCount"),
            spotify_current_play_count=data.get("spotifyCurrentPlayCount"),
            total_current_play_count=data.get("totalCurrentPlayCount"),
            youtube_current_play_count_abbreviated=data.get("youtubeCurrentPlayCountAbbreviated"),
            spotify_current_play_count_abbreviated=data.get("spotifyCurrentPlayCountAbbreviated"),
            total_current_play_count_abbreviated=data.get("totalCurrentPlayCountAbbreviated"),
            total_weekly_change_percentage=data.get("totalWeeklyChangePercentage"),
            total_weekly_change_percentage_formatted=data.get("totalWeeklyChangePercentageFormatted"),
        )


class Rank(BaseModel):
    """Domain model for Rank data."""

    name: str
    display_name: str
    sort_field: str
    sort_order: str
    is_default: bool
    data_field: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "sortField": self.sort_field,
            "sortOrder": self.sort_order,
            "isDefault": self.is_default,
            "dataField": self.data_field,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            name=data["name"],
            display_name=data["displayName"],
            sort_field=data["sortField"],
            sort_order=data["sortOrder"],
            is_default=data["isDefault"],
            data_field=data["dataField"],
        )

    @classmethod
    def from_django_model(cls, django_rank) -> Self:
        """Convert from Django RankModel."""
        from core.constants import DEFAULT_RANK_TYPE

        return cls(
            name=django_rank.name,
            display_name=django_rank.display_name,
            sort_field=django_rank.sort_field,
            sort_order=django_rank.sort_order,
            is_default=django_rank.name == DEFAULT_RANK_TYPE.value,
            data_field=django_rank.data_field,
        )


class Service(BaseModel):
    """Domain model for Service data."""

    id: int
    name: str
    display_name: str
    icon_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "displayName": self.display_name,
            "iconUrl": self.icon_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data["displayName"],
            icon_url=data["iconUrl"],
        )

    @classmethod
    def from_django_model(cls, django_service) -> Self:
        """Convert from Django ServiceModel."""
        return cls(
            id=django_service.id,
            name=django_service.name,
            display_name=django_service.display_name,
            icon_url=django_service.icon_url,
        )


class Genre(BaseModel):
    """Domain model for Genre data."""

    id: int
    name: str
    display_name: str
    icon_class: str
    icon_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "displayName": self.display_name,
            "iconClass": self.icon_class,
            "iconUrl": self.icon_url,
        }

    def to_dict_with_button_labels(self, button_labels: list[ButtonLabel]) -> dict[str, Any]:
        """Convert to dict with button labels included."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "icon_url": self.icon_url,
            "button_labels": [bl.to_dict() for bl in button_labels],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data["displayName"],
            icon_class=data["iconClass"],
            icon_url=data["iconUrl"],
        )

    @classmethod
    def from_django_model(cls, django_genre) -> Self:
        """Convert from Django GenreModel."""
        # Import inside method to avoid circular dependency

        return cls(
            id=django_genre.id,
            name=django_genre.name,
            display_name=django_genre.display_name,
            icon_class=django_genre.icon_class,
            icon_url=django_genre.icon_url,
        )


class RawPlaylistData(BaseModel):
    """Domain model for RawPlaylistData."""

    id: int
    genre_id: int
    service_id: int
    playlist_url: str
    playlist_name: str | None = None
    playlist_cover_url: str | None = None
    playlist_cover_description_text: str | None = None
    data: list[dict[str, Any]] | dict[str, Any]
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "genreId": self.genre_id,
            "serviceId": self.service_id,
            "playlistUrl": self.playlist_url,
            "playlistName": self.playlist_name,
            "playlistCoverUrl": self.playlist_cover_url,
            "playlistCoverDescriptionText": self.playlist_cover_description_text,
            "data": self.data,
            "createdAt": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            genre_id=data["genreId"],
            service_id=data["serviceId"],
            playlist_url=data["playlistUrl"],
            playlist_name=data.get("playlistName"),
            playlist_cover_url=data.get("playlistCoverUrl"),
            playlist_cover_description_text=data.get("playlistCoverDescriptionText"),
            data=data["data"],
            created_at=datetime.fromisoformat(data["createdAt"]),
        )

    @classmethod
    def from_django_model(cls, django_raw_playlist) -> Self:
        """Convert from Django RawPlaylistDataModel."""
        return cls(
            id=django_raw_playlist.id,
            genre_id=django_raw_playlist.genre.id,
            service_id=django_raw_playlist.service.id,
            playlist_url=django_raw_playlist.playlist_url,
            playlist_name=django_raw_playlist.playlist_name,
            playlist_cover_url=django_raw_playlist.playlist_cover_url,
            playlist_cover_description_text=django_raw_playlist.playlist_cover_description_text,
            data=django_raw_playlist.data,
            created_at=django_raw_playlist.created_at,
        )


@dataclass
class ServiceConfig:
    name: str
    display_name: str
    service_url: str
    description: str
    example_track_search: str
    example_playlist_search: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "serviceUrl": self.service_url,
            "description": self.description,
            "exampleTrackSearch": self.example_track_search,
            "examplePlaylistSearch": self.example_playlist_search,
        }


@dataclass
class IframeConfig:
    service_name: str
    embed_base_url: str
    embed_params: str | None
    allow: str
    height: int
    referrer_policy: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "embed_base_url": self.embed_base_url,
            "embed_params": self.embed_params,
            "allow": self.allow,
            "height": self.height,
            "referrer_policy": self.referrer_policy,
        }


@dataclass
class ServicePlayCount:
    current_play_count: int | None
    weekly_change_percentage: float | None
    updated_at: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_play_count": self.current_play_count,
            "weekly_change_percentage": self.weekly_change_percentage,
            "updated_at": self.updated_at,
            "current_play_count_abbreviated": format_play_count(self.current_play_count)
            if self.current_play_count
            else None,
            "weekly_change_percentage_formatted": format_percentage_change(self.weekly_change_percentage)
            if self.weekly_change_percentage
            else None,
        }


@dataclass
class TrackPlayCountData:
    isrc: str
    spotify: ServicePlayCount
    apple_music: ServicePlayCount
    youtube: ServicePlayCount
    soundcloud: ServicePlayCount
    total_current_play_count: int | None
    total_weekly_change_percentage: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "isrc": self.isrc,
            "spotify_current_play_count": self.spotify.current_play_count,
            "spotify_weekly_change_percentage": self.spotify.weekly_change_percentage,
            "spotify_updated_at": self.spotify.updated_at,
            "spotify_current_play_count_abbreviated": self.spotify.to_dict()["current_play_count_abbreviated"],
            "spotify_weekly_change_percentage_formatted": self.spotify.to_dict()["weekly_change_percentage_formatted"],
            "apple_music_current_play_count": self.apple_music.current_play_count,
            "apple_music_weekly_change_percentage": self.apple_music.weekly_change_percentage,
            "apple_music_updated_at": self.apple_music.updated_at,
            "apple_music_current_play_count_abbreviated": self.apple_music.to_dict()["current_play_count_abbreviated"],
            "apple_music_weekly_change_percentage_formatted": self.apple_music.to_dict()[
                "weekly_change_percentage_formatted"
            ],
            "youtube_current_play_count": self.youtube.current_play_count,
            "youtube_weekly_change_percentage": self.youtube.weekly_change_percentage,
            "youtube_updated_at": self.youtube.updated_at,
            "youtube_current_play_count_abbreviated": self.youtube.to_dict()["current_play_count_abbreviated"],
            "youtube_weekly_change_percentage_formatted": self.youtube.to_dict()["weekly_change_percentage_formatted"],
            "soundcloud_current_play_count": self.soundcloud.current_play_count,
            "soundcloud_weekly_change_percentage": self.soundcloud.weekly_change_percentage,
            "soundcloud_updated_at": self.soundcloud.updated_at,
            "soundcloud_current_play_count_abbreviated": self.soundcloud.to_dict()["current_play_count_abbreviated"],
            "soundcloud_weekly_change_percentage_formatted": self.soundcloud.to_dict()[
                "weekly_change_percentage_formatted"
            ],
            "total_current_play_count": self.total_current_play_count,
            "total_weekly_change_percentage": self.total_weekly_change_percentage,
            "total_current_play_count_abbreviated": format_play_count(self.total_current_play_count)
            if self.total_current_play_count
            else None,
            "total_weekly_change_percentage_formatted": format_percentage_change(self.total_weekly_change_percentage)
            if self.total_weekly_change_percentage
            else None,
        }


@dataclass
class PlaylistMetadata:
    playlist_name: str
    playlist_cover_url: str
    playlist_cover_description_text: str
    playlist_url: str
    genre_name: str
    service_name: str
    service_icon_url: str

    @classmethod
    def from_raw_playlist_and_service(cls, raw_playlist, service, genre: str) -> "PlaylistMetadata":
        """Create PlaylistMetadata from raw playlist data and service info."""
        # For TuneMeld service, require proper curated descriptions - no fallbacks
        if service.name == "tunemeld" and not raw_playlist.playlist_cover_description_text:
            raise ValueError(
                f"Missing curated description for TuneMeld {genre} playlist. "
                f"Raw playlist data: {raw_playlist.playlist_cover_description_text}. "
                f"This indicates the ETL pipeline has not run or failed to generate proper descriptions."
            )

        return cls(
            playlist_name=raw_playlist.playlist_name or f"{service.display_name} {genre} Playlist",
            playlist_cover_url=raw_playlist.playlist_cover_url or "",
            playlist_cover_description_text=raw_playlist.playlist_cover_description_text
            or f"Curated {genre} tracks from {service.display_name}",
            playlist_url=raw_playlist.playlist_url,
            genre_name=genre,
            service_name=service.name,
            service_icon_url=service.icon_url,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "playlist_name": self.playlist_name,
            "playlist_cover_url": self.playlist_cover_url,
            "playlist_cover_description_text": self.playlist_cover_description_text,
            "playlist_url": self.playlist_url,
            "genre_name": self.genre_name,
            "service_name": self.service_name,
            "service_icon_url": self.service_icon_url,
        }


@dataclass
class RankData:
    name: str
    display_name: str
    sort_field: str
    sort_order: str
    is_default: bool
    data_field: str

    @classmethod
    def from_rank(cls, rank) -> "RankData":
        """Create RankData from rank object."""
        return cls(
            name=rank.name,
            display_name=rank.display_name,
            sort_field=rank.sort_field,
            sort_order=rank.sort_order,
            is_default=rank.is_default,
            data_field=rank.data_field,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "sort_field": self.sort_field,
            "sort_order": self.sort_order,
            "is_default": self.is_default,
            "data_field": self.data_field,
        }


@dataclass
class ServiceConfigWithLabels:
    name: str
    display_name: str
    icon_url: str
    url_field: str | None
    source_field: str | None
    button_labels: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "icon_url": self.icon_url,
            "url_field": self.url_field,
            "source_field": self.source_field,
            "button_labels": self.button_labels,
        }


@dataclass
class ButtonLabelData:
    button_type: str
    context: str
    title: str
    aria_label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "buttonType": self.button_type,
            "context": self.context,
            "title": self.title,
            "ariaLabel": self.aria_label,
        }
