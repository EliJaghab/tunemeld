from typing import Any

from core.api.genre_service_api import get_service, get_track_rank_by_track_object, is_track_seen_on_service
from core.api.track_metadata_api import build_track_query_url
from core.constants import ServiceName
from core.graphql.button_labels import generate_track_button_labels
from core.models.track import Track


class TrackEnrichmentService:
    """Service for bulk enriching track data with computed fields."""

    @staticmethod
    def enrich_tracks_bulk(tracks: list[Track], genre: str, service: str) -> list[dict[str, Any]]:
        """
        Bulk enrich tracks with all computed fields needed for GraphQL responses.

        Args:
            tracks: List of Track objects to enrich
            genre: Genre context for computations
            service: Service context for computations

        Returns:
            List of enriched track data dictionaries
        """
        enriched_tracks = []

        for track in tracks:
            enriched_data = TrackEnrichmentService._enrich_single_track(track, genre, service)
            enriched_tracks.append(enriched_data)

        return enriched_tracks

    @staticmethod
    def _enrich_single_track(track: Track, genre: str, service: str) -> dict[str, Any]:
        """Enrich a single track with all computed fields."""

        # Basic track data
        track_data = {
            "id": track.id,
            "isrc": track.isrc,
            "track_name": track.track_name,
            "artist_name": track.artist_name,
            "album_name": track.album_name,
            "spotify_url": track.spotify_url,
            "apple_music_url": track.apple_music_url,
            "youtube_url": track.youtube_url,
            "soundcloud_url": track.soundcloud_url,
            "album_cover_url": track.album_cover_url,
            "aggregate_rank": track.aggregate_rank,
            "aggregate_score": track.aggregate_score,
            "updated_at": track.updated_at.isoformat() if track.updated_at else None,
            "tunemeld_rank": getattr(track, "tunemeld_rank", None),
        }

        # Add enrichment data
        track_data.update(
            {
                "button_labels": TrackEnrichmentService._get_button_labels(track, genre, service),
                "spotify_source": TrackEnrichmentService._get_service_source(track, ServiceName.SPOTIFY),
                "apple_music_source": TrackEnrichmentService._get_service_source(track, ServiceName.APPLE_MUSIC),
                "soundcloud_source": TrackEnrichmentService._get_service_source(track, ServiceName.SOUNDCLOUD),
                "youtube_source": TrackEnrichmentService._get_service_source(track, ServiceName.YOUTUBE),
                "seen_on_spotify": TrackEnrichmentService._is_seen_on_service(track, genre, ServiceName.SPOTIFY),
                "seen_on_apple_music": TrackEnrichmentService._is_seen_on_service(
                    track, genre, ServiceName.APPLE_MUSIC
                ),
                "seen_on_soundcloud": TrackEnrichmentService._is_seen_on_service(track, genre, ServiceName.SOUNDCLOUD),
                "spotify_rank": TrackEnrichmentService._get_service_rank(track, genre, ServiceName.SPOTIFY),
                "apple_music_rank": TrackEnrichmentService._get_service_rank(track, genre, ServiceName.APPLE_MUSIC),
                "soundcloud_rank": TrackEnrichmentService._get_service_rank(track, genre, ServiceName.SOUNDCLOUD),
                "track_detail_url_spotify": TrackEnrichmentService._get_track_detail_url(track, genre, "spotify"),
                "track_detail_url_apple_music": TrackEnrichmentService._get_track_detail_url(
                    track, genre, "apple_music"
                ),
                "track_detail_url_soundcloud": TrackEnrichmentService._get_track_detail_url(track, genre, "soundcloud"),
                "track_detail_url_youtube": TrackEnrichmentService._get_track_detail_url(track, genre, "youtube"),
            }
        )

        return track_data

    @staticmethod
    def _get_button_labels(track: Track, genre: str, service: str) -> list[dict[str, str]]:
        """Get button labels for track."""
        try:
            button_labels = generate_track_button_labels(track, genre=genre, service=service)
            if button_labels:
                return [
                    {"buttonType": bl.buttonType, "context": bl.context, "title": bl.title, "ariaLabel": bl.ariaLabel}
                    for bl in button_labels
                ]
        except Exception:
            pass
        return []

    @staticmethod
    def _get_service_source(track: Track, service_name: ServiceName) -> dict[str, str] | None:
        """Get service source data for track."""
        url_field = f"{service_name.value}_url"
        track_url = getattr(track, url_field, None)

        if not track_url:
            return None

        try:
            service = get_service(service_name)
            if not service:
                return None
            return {
                "name": service_name.value,
                "display_name": service.display_name,
                "url": track_url,
                "icon_url": service.icon_url,
            }
        except Exception:
            return None

    @staticmethod
    def _is_seen_on_service(track: Track, genre: str, service_name: ServiceName) -> bool:
        """Check if track was seen on service for genre."""
        try:
            return is_track_seen_on_service(track.isrc, genre, service_name)
        except Exception:
            return False

    @staticmethod
    def _get_service_rank(track: Track, genre: str, service_name: ServiceName) -> int | None:
        """Get track rank for service/genre."""
        try:
            return get_track_rank_by_track_object(track, genre, service_name.value)
        except Exception:
            return None

    @staticmethod
    def _get_track_detail_url(track: Track, genre: str, player: str) -> str:
        """Get track detail URL for player."""
        try:
            url = build_track_query_url(genre, "tunemeld-rank", track.isrc, player)
            return url if url else f"/?genre={genre}&rank=tunemeld-rank&player={player}&isrc={track.isrc}"
        except Exception:
            return f"/?genre={genre}&rank=tunemeld-rank&player={player}&isrc={track.isrc}"
