import graphene
from core.api.genre_service_api import get_genre, get_service
from core.constants import ServiceName
from core.graphql.track import TrackType
from core.models import Track
from core.models.play_counts import AggregatePlayCount
from core.models.playlist import Playlist, Rank, RawPlaylistData
from core.utils.local_cache import CachePrefix, local_cache_get, local_cache_set


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

    @staticmethod
    def _enrich_tracks_with_play_counts(tracks):
        """Pre-populate track objects with play count data to avoid individual cache calls."""
        if not tracks:
            return tracks

        track_isrcs = [track.isrc for track in tracks]

        youtube_service = get_service(ServiceName.YOUTUBE)
        spotify_service = get_service(ServiceName.SPOTIFY)
        soundcloud_service = get_service(ServiceName.SOUNDCLOUD)

        if not all([youtube_service, spotify_service, soundcloud_service]):
            return tracks

        youtube_counts = {
            vc.isrc: vc
            for vc in AggregatePlayCount.objects.filter(isrc__in=track_isrcs, service=youtube_service)
            .order_by("isrc", "-recorded_date")
            .distinct("isrc")
        }

        spotify_counts = {
            vc.isrc: vc
            for vc in AggregatePlayCount.objects.filter(isrc__in=track_isrcs, service=spotify_service)
            .order_by("isrc", "-recorded_date")
            .distinct("isrc")
        }

        soundcloud_counts = {
            vc.isrc: vc
            for vc in AggregatePlayCount.objects.filter(isrc__in=track_isrcs, service=soundcloud_service)
            .order_by("isrc", "-recorded_date")
            .distinct("isrc")
        }

        for track in tracks:
            youtube_data = youtube_counts.get(track.isrc)
            spotify_data = spotify_counts.get(track.isrc)
            soundcloud_data = soundcloud_counts.get(track.isrc)

            track._youtube_current_play_count = youtube_data.current_play_count if youtube_data else None
            track._spotify_current_play_count = spotify_data.current_play_count if spotify_data else None
            track._soundcloud_current_play_count = soundcloud_data.current_play_count if soundcloud_data else None
            track._youtube_play_count_delta_percentage = youtube_data.weekly_change_percentage if youtube_data else None
            track._spotify_play_count_delta_percentage = spotify_data.weekly_change_percentage if spotify_data else None
            track._soundcloud_play_count_delta_percentage = (
                soundcloud_data.weekly_change_percentage if soundcloud_data else None
            )

        return tracks

    def resolve_service_order(self, info):
        """Used to order the header art."""
        return [ServiceName.SOUNDCLOUD, ServiceName.APPLE_MUSIC, ServiceName.SPOTIFY]

    def resolve_playlist(self, info, genre, service):
        """Get playlist data for any service (including Aggregate) and genre."""
        from django.conf import settings

        cache_key_data = f"resolve_playlist:genre={genre}:service={service}"

        # Skip cache in development to always get fresh percentage data
        cached_result = None
        if settings.ENVIRONMENT != "dev":
            cached_result = local_cache_get(CachePrefix.GQL_PLAYLIST, cache_key_data)

        if cached_result is not None:
            # Reconstruct Track objects from cached data for GraphQL compatibility
            cached_tracks = []
            for track_data in cached_result["tracks"]:
                track = Track()
                track._state.adding = False
                track._state.db = "default"

                # Set all cached attributes (both model fields and enrichment data)
                for key, value in track_data.items():
                    if key == "updated_at" and isinstance(value, str):
                        # Convert ISO string back to datetime
                        from datetime import datetime

                        setattr(track, key, datetime.fromisoformat(value))
                    else:
                        setattr(track, key, value)

                cached_tracks.append(track)

            return PlaylistType(
                genre_name=cached_result["genre_name"], service_name=cached_result["service_name"], tracks=cached_tracks
            )

        playlists = Playlist.objects.filter(genre__name=genre, service__name=service).order_by("position")

        tracks = []
        for playlist_entry in playlists:
            if playlist_entry.isrc:
                try:
                    track = Track.objects.get(isrc=playlist_entry.isrc)
                    tracks.append(track)
                except Track.DoesNotExist:
                    continue

        tracks = PlaylistQuery._enrich_tracks_with_play_counts(tracks)

        serialized_tracks = []
        for track in tracks:
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
                "_youtube_current_play_count": getattr(track, "_youtube_current_play_count", None),
                "_spotify_current_play_count": getattr(track, "_spotify_current_play_count", None),
                "_soundcloud_current_play_count": getattr(track, "_soundcloud_current_play_count", None),
                "_youtube_play_count_delta_percentage": getattr(track, "_youtube_play_count_delta_percentage", None),
                "_spotify_play_count_delta_percentage": getattr(track, "_spotify_play_count_delta_percentage", None),
                "_soundcloud_play_count_delta_percentage": getattr(
                    track, "_soundcloud_play_count_delta_percentage", None
                ),
            }
            serialized_tracks.append(track_data)

        cache_data = {"genre_name": genre, "service_name": service, "tracks": serialized_tracks}
        # Skip caching in development to always get fresh percentage data
        if settings.ENVIRONMENT != "dev":
            local_cache_set(CachePrefix.GQL_PLAYLIST, cache_key_data, cache_data)

        return PlaylistType(genre_name=genre, service_name=service, tracks=tracks)

    def resolve_playlists_by_genre(self, info, genre):
        """Get playlist metadata for all services for a given genre."""
        genre_obj = get_genre(genre)
        if not genre_obj:
            return []

        raw_playlists = (
            RawPlaylistData.objects.filter(genre=genre_obj)
            .select_related("service", "genre")
            .order_by("service_id", "-created_at")
            .distinct("service_id")
        )

        playlist_metadata = []
        for raw_playlist in raw_playlists:
            playlist_metadata.append(
                PlaylistMetadataType(
                    playlist_name=raw_playlist.playlist_name or f"{raw_playlist.service.display_name} {genre} Playlist",
                    playlist_cover_url=raw_playlist.playlist_cover_url or "",
                    playlist_cover_description_text=raw_playlist.playlist_cover_description_text
                    or f"Curated {genre} tracks from {raw_playlist.service.display_name}",
                    playlist_url=raw_playlist.playlist_url,
                    genre_name=genre,
                    service_name=raw_playlist.service.name,
                    service_icon_url=raw_playlist.service.icon_url,
                )
            )

        return playlist_metadata

    def resolve_updated_at(self, info, genre):
        """Get the update timestamp of the TuneMeld playlist for a genre."""
        playlist_entry = (
            Playlist.objects.filter(genre__name=genre, service__name=ServiceName.TUNEMELD)
            .select_related("service_track__track")
            .first()
        )

        if playlist_entry and playlist_entry.service_track and playlist_entry.service_track.track:
            return playlist_entry.service_track.track.updated_at

        return None

    def resolve_ranks(self, info):
        """Get playlist ranking options."""
        from core.constants import DEFAULT_RANK_TYPE

        ranks = Rank.objects.all().order_by("id")

        return [
            RankType(
                display_name=rank.display_name,
                sort_field=rank.sort_field,
                sort_order=rank.sort_order,
                is_default=rank.name == DEFAULT_RANK_TYPE.value,
                data_field=rank.data_field,
            )
            for rank in ranks
        ]
