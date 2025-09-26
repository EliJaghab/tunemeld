from datetime import datetime

import graphene
from core.api.genre_service_api import get_genre, get_raw_playlist_data_by_genre_service, get_service
from core.constants import DEFAULT_RANK_TYPE, ServiceName
from core.graphql.track import TrackType
from core.models import Service, Track
from core.models.playlist import Playlist, Rank
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

    def resolve_service_order(self, info):
        """Used to order the header art and individual playlist columns."""
        service_names = [ServiceName.APPLE_MUSIC.value, ServiceName.SOUNDCLOUD.value, ServiceName.SPOTIFY.value]
        services = []
        for name in service_names:
            service = get_service(name)
            if service:
                services.append(service.name)
        return services

    def resolve_playlist(self, info, genre, service):
        """Get playlist data for any service (including Aggregate) and genre."""
        cache_key_data = f"resolve_playlist:genre={genre}:service={service}"
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
                track = Track.objects.filter(isrc=playlist_entry.isrc).order_by("-id").first()
                if track:
                    tracks.append(track)

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
            }
            serialized_tracks.append(track_data)

        cache_data = {"genre_name": genre, "service_name": service, "tracks": serialized_tracks}
        local_cache_set(CachePrefix.GQL_PLAYLIST, cache_key_data, cache_data)

        return PlaylistType(genre_name=genre, service_name=service, tracks=tracks)

    def resolve_playlists_by_genre(self, info, genre):
        """Get playlist metadata for all services for a given genre."""
        genre_obj = get_genre(genre)
        if not genre_obj:
            return []

        raw_playlists = []
        services = Service.objects.values_list("name", flat=True).distinct()
        for service_name in services:
            raw_playlist = get_raw_playlist_data_by_genre_service(genre, service_name)
            if raw_playlist:
                raw_playlists.append(raw_playlist)

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
