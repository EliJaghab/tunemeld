"""
Domain models for TuneMeld - pure business logic without Django dependencies.

These models mirror the frontend TypeScript types exactly and provide
clean serialization/deserialization for GraphQL and cache layers.
"""

from datetime import datetime
from typing import Any

from core.constants import ServiceName
from core.models.track import TrackModel
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
            "buttonType": self.button_type,
            "context": self.context,
            "title": self.title,
            "ariaLabel": self.aria_label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ButtonLabel":
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
    def from_dict(cls, data: dict[str, Any]) -> "ServiceSource":
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

    # Service presence flags
    seen_on_spotify: bool = False
    seen_on_apple_music: bool = False
    seen_on_soundcloud: bool = False

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
            "seenOnSpotify": self.seen_on_spotify,
            "seenOnAppleMusic": self.seen_on_apple_music,
            "seenOnSoundcloud": self.seen_on_soundcloud,
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
    def from_dict(cls, data: dict[str, Any]) -> "Track":
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
            seen_on_spotify=data.get("seenOnSpotify", False),
            seen_on_apple_music=data.get("seenOnAppleMusic", False),
            seen_on_soundcloud=data.get("seenOnSoundcloud", False),
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
    def from_django_model(
        cls, django_track: TrackModel, genre: str | None = None, service: str | None = None
    ) -> "Track":
        """Convert from Django TrackModel with full enrichment."""
        if not isinstance(django_track, TrackModel):
            raise TypeError("Expected Django TrackModel")

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
    def _enrich_track_data(cls, track: TrackModel, genre: str, service: str) -> dict[str, Any]:
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

        # Seen on service flags
        enrichment.update(
            {
                "seenOnSpotify": cls._is_seen_on_service(track, genre, ServiceName.SPOTIFY),
                "seenOnAppleMusic": cls._is_seen_on_service(track, genre, ServiceName.APPLE_MUSIC),
                "seenOnSoundcloud": cls._is_seen_on_service(track, genre, ServiceName.SOUNDCLOUD),
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
    def _build_service_source(track: TrackModel, service_name: ServiceName) -> ServiceSource | None:
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
    def _get_service_rank(track: TrackModel, genre: str, service_name: ServiceName) -> int | None:
        """Get track rank for service/genre."""
        from core.api.genre_service_api import get_track_rank_by_track_object

        try:
            return get_track_rank_by_track_object(track, genre, service_name.value)
        except Exception:
            return None

    @staticmethod
    def _is_seen_on_service(track: TrackModel, genre: str, service_name: ServiceName) -> bool:
        """Check if track was seen on service for genre."""
        from core.api.genre_service_api import is_track_seen_on_service

        try:
            return is_track_seen_on_service(track.isrc, genre, service_name)
        except Exception:
            return False

    @staticmethod
    def _build_track_detail_url(track: TrackModel, genre: str, player: str) -> str:
        """Build track detail URL for player."""
        from core.api.track_metadata_api import build_track_query_url

        try:
            url = build_track_query_url(genre, "tunemeld-rank", track.isrc, player)
            return url if url else f"/?genre={genre}&rank=tunemeld-rank&player={player}&isrc={track.isrc}"
        except Exception:
            return f"/?genre={genre}&rank=tunemeld-rank&player={player}&isrc={track.isrc}"

    @staticmethod
    def _get_button_labels(track: TrackModel, genre: str, service: str) -> list[ButtonLabel]:
        """Get button labels for track."""
        try:
            from core.graphql.button_labels import generate_track_button_labels

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
    def from_dict(cls, data: dict[str, Any]) -> "Playlist":
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
    def from_dict(cls, data: dict[str, Any]) -> "PlayCount":
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
    def from_dict(cls, data: dict[str, Any]) -> "Rank":
        return cls(
            name=data["name"],
            display_name=data["displayName"],
            sort_field=data["sortField"],
            sort_order=data["sortOrder"],
            is_default=data["isDefault"],
            data_field=data["dataField"],
        )

    @classmethod
    def from_django_model(cls, django_rank) -> "Rank":
        """Convert from Django RankModel."""
        from core.constants import DEFAULT_RANK_TYPE
        from core.models.playlist import RankModel

        if not isinstance(django_rank, RankModel):
            raise TypeError("Expected Django RankModel")

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
    def from_dict(cls, data: dict[str, Any]) -> "Service":
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data["displayName"],
            icon_url=data["iconUrl"],
        )

    @classmethod
    def from_django_model(cls, django_service) -> "Service":
        """Convert from Django ServiceModel."""
        from core.models.genre_service import ServiceModel

        if not isinstance(django_service, ServiceModel):
            raise TypeError("Expected Django ServiceModel")

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Genre":
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data["displayName"],
            icon_class=data["iconClass"],
            icon_url=data["iconUrl"],
        )

    @classmethod
    def from_django_model(cls, django_genre) -> "Genre":
        """Convert from Django GenreModel."""
        from core.models.genre_service import GenreModel

        if not isinstance(django_genre, GenreModel):
            raise TypeError("Expected Django GenreModel")

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
    data: dict[str, Any]
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
    def from_dict(cls, data: dict[str, Any]) -> "RawPlaylistData":
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
    def from_django_model(cls, django_raw_playlist) -> "RawPlaylistData":
        """Convert from Django RawPlaylistDataModel."""
        from core.models.playlist import RawPlaylistDataModel

        if not isinstance(django_raw_playlist, RawPlaylistDataModel):
            raise TypeError("Expected Django RawPlaylistDataModel")

        # Handle legacy data format: if data is a list (old format), convert to new format
        data = django_raw_playlist.data
        if isinstance(data, list):
            # Legacy format: data was just the tracks list
            # Convert to new format with metadata and tracks structure
            data = {
                "metadata": {
                    "playlist_url": django_raw_playlist.playlist_url,
                    "playlist_name": django_raw_playlist.playlist_name,
                    "playlist_cover_url": django_raw_playlist.playlist_cover_url,
                    "playlist_cover_description_text": django_raw_playlist.playlist_cover_description_text,
                },
                "tracks": data,
            }

        return cls(
            id=django_raw_playlist.id,
            genre_id=django_raw_playlist.genre.id,
            service_id=django_raw_playlist.service.id,
            playlist_url=django_raw_playlist.playlist_url,
            playlist_name=django_raw_playlist.playlist_name,
            playlist_cover_url=django_raw_playlist.playlist_cover_url,
            playlist_cover_description_text=django_raw_playlist.playlist_cover_description_text,
            data=data,
            created_at=django_raw_playlist.created_at,
        )
